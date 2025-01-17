#!/usr/bin/env python
"""
A python command line tool to turn E3SM model output into CMIP6 compatable data
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
from e3sm_to_cmip.lib import run_serial
from e3sm_to_cmip.lib import run_parallel
from e3sm_to_cmip.util import precheck
from e3sm_to_cmip.util import print_debug
from e3sm_to_cmip.util import copy_user_metadata
from e3sm_to_cmip.util import add_metadata
from e3sm_to_cmip.util import load_handlers
from e3sm_to_cmip.util import print_var_info
from e3sm_to_cmip.util import parse_arguments
from e3sm_to_cmip.util import print_message
from e3sm_to_cmip import resources
from e3sm_to_cmip import cmor_handlers

import os
import sys
import logging
import tempfile
import threading
import signal
from concurrent.futures import ProcessPoolExecutor as Pool

os.environ['CDAT_ANONYMOUS_LOG'] = 'false'


np.warnings.filterwarnings('ignore')


def timeout_exit():
    print_message("Hit timeout limit, exiting")
    os.kill(os.getpid(), signal.SIGINT)


def main():

    # parse the command line arguments
    _args = parse_arguments().__dict__

    if len(_args.get('var_list')) == 1 and " " in _args.get('var_list')[0]:
        var_list = _args.get('var_list')[0].split()
    else:
        var_list = _args.get('var_list')
    var_list = [x.strip(',') for x in var_list]
    input_path = _args.get('input_path')
    output_path = _args.get('output_path')
    tables_path = _args.get('tables_path')
    user_metadata = _args.get('user_metadata')
    custom_metadata = _args.get('custom_metadata')
    nproc = _args.get('num_proc')
    serial = _args.get('serial')
    realm = _args.get('realm')
    debug = True if _args.get('debug') else False
    map_path = _args.get('map')
    cmor_log_dir = _args.get('logdir')
    timeout = int(_args.get('timeout')) if _args.get('timeout') else False
    simple = _args.get('simple', False)
    precheck_path = _args.get('precheck', False)
    freq = _args.get('freq')

    if simple:
        no_metadata = True
        if not tables_path:
            resource_path, _ = os.path.split(os.path.abspath(resources.__file__))
            tables_path = resource_path

    timer = None
    if timeout:
        timer = threading.Timer(timeout, timeout_exit)
        timer.start()

    if _args.get('handlers'):
        handlers_path = os.path.abspath(_args.get('handlers'))
    else:
        handlers_path, _ = os.path.split(
            os.path.abspath(cmor_handlers.__file__))

    if precheck_path:
        new_var_list = precheck(input_path, precheck_path, var_list, realm)
        if not new_var_list:
            print("All variables previously computed")
            os.mkdir(os.path.join(output_path, 'CMIP6'))
            if timer:
                timer.cancel()
            return 0
        else:
            print_message(
                f"Setting up conversion for {' '.join(new_var_list)}", 'ok')
            var_list = new_var_list
    
    # load variable handlers
    handlers = load_handlers(
        handlers_path=handlers_path,
        var_list=var_list,
        freq=freq,
        realm=realm,
        tables=tables_path,
        simple=simple)

    if len(handlers) == 0:
        print_message('No handlers loaded')
        sys.exit(1)
    if _args.get('info'):
        print_var_info(
            handlers,
            freq,
            input_path,
            tables_path,
            _args.get('info_out'))
        sys.exit(0)

    new_metadata_path = os.path.join(
        output_path,
        'user_metadata.json')

    # create the output dir if it doesnt exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # setup temp storage directory
    temp_path = os.environ.get('TMPDIR')
    if temp_path is None:

        temp_path = f'{output_path}/tmp'
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

    tempfile.tempdir = temp_path

    logging_path = os.path.join(output_path, 'converter.log')
    print_message(f"Writing log output to: {logging_path}", 'debug')

    # setup logging
    logging.basicConfig(
        format='%(asctime)s:%(levelname)s: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        filename=logging_path,
        filemode='w',
        level=logging.INFO)

    # copy the users metadata json file with the updated output directory
    if not simple:
        copy_user_metadata(
            user_metadata, output_path)

    # run in the user-selected mode
    if serial:
        print_message('Running CMOR handlers in serial', 'ok')
        try:
            status = run_serial(
                handlers=handlers,
                input_path=input_path,
                tables_path=tables_path,
                metadata_path=new_metadata_path,
                map_path=map_path,
                realm=realm,
                logdir=cmor_log_dir,
                simple=simple,
                outpath=output_path,
                freq=freq)
        except KeyboardInterrupt as error:
            print_message(' -- keyboard interrupt -- ', 'error')
            return 1
        except Exception as e:
            print_debug(e)
            return 1
    else:
        print_message('Running CMOR handlers in parallel', 'ok')
        try:
            pool = Pool(max_workers=nproc)
            status = run_parallel(
                pool=pool,
                handlers=handlers,
                input_path=input_path,
                tables_path=tables_path,
                metadata_path=new_metadata_path,
                map_path=map_path,
                realm=realm,
                logdir=cmor_log_dir,
                simple=simple,
                outpath=output_path,
                freq=freq)
        except KeyboardInterrupt as error:
            print_message(' -- keyboard interrupt -- ', 'error')
            return 1
        except Exception as error:
            print_debug(error)
            return 1
    if status != 0:
        print_message(
            f"Error running handlers: { ' '.join([x['name'] for x in handlers]) }")
        return 1

    if custom_metadata:
        add_metadata(
            file_path=output_path,
            var_list=var_list,
            metadata=custom_metadata)

    if timeout:
        timer.cancel()
    return 0
# ------------------------------------------------------------------


if __name__ == "__main__":
    sys.exit(main())
