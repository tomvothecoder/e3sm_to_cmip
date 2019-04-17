"""
FSDSC, FSNSC to rsuscs converter
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import cmor
import cdms2
import logging

from tqdm import tqdm
from e3sm_to_cmip.util import print_message
from e3sm_to_cmip.util import get_dimension_data
from e3sm_to_cmip.util import setup_cmor
from e3sm_to_cmip.util import load_axis
from e3sm_to_cmip.lib import handle_variables

# list of raw variable names needed
RAW_VARIABLES = [str('FSDSC'), str('FSNSC')]
VAR_NAME = str('rsuscs')
VAR_UNITS = str('W m-2')
TABLE = str('CMIP6_Amon.json')
POSITIVE = str('up')

def write_data(varid, data, timeval, timebnds, index):
    """
    rsuscs = FSDSC - FSNSC
    """
    outdata = data['FSDSC'][index, :] - data['FSNSC'][index, :]
    cmor.write(
        varid,
        outdata,
        time_vals=timeval,
        time_bnds=timebnds)
# ------------------------------------------------------------------

def handle(infiles, tables, user_input_path, serial=None):
    """
    Parameters
    ----------
        infiles (List): a list of strings of file names for the raw input data
        tables (str): path to CMOR tables
        user_input_path (str): path to user input json file
    Returns
    -------
        var name (str): the name of the processed variable after processing is complete
    """

    handle_variables(
        metadata_path=user_input_path,
        tables=tables,
        table=TABLE,
        infiles=infiles,
        raw_variables=RAW_VARIABLES,
        write_data=write_data,
        outvar_name=VAR_NAME,
        outvar_units=VAR_UNITS,
        serial=serial,
        positive=POSITIVE)

    return VAR_NAME
# ------------------------------------------------------------------
