
"""
Fraction of time steps with sea ice, sitimefrac
"""

from __future__ import absolute_import, division, print_function

import xarray
import logging

from e3sm_to_cmip import mpas
from e3sm_to_cmip.util import print_message
# 'MPAS' as a placeholder for raw variables needed
RAW_VARIABLES = ['MPASSI', 'MPAS_mesh', 'MPAS_map']

# output variable name
VAR_NAME = 'sitimefrac'
VAR_UNITS = '1'
TABLE = 'CMIP6_SImon.json'


def handle(infiles, tables, user_input_path, **kwargs):
    """
    Transform MPASSI timeMonthly_avg_icePresent into CMIP.sitimefrac

    Parameters
    ----------
    infiles : dict
        a dictionary with namelist, mesh and time series file names

    tables : str
        path to CMOR tables

    user_input_path : str
        path to user input json file

    Returns
    -------
    varname : str
        the name of the processed variable after processing is complete
    """
    if kwargs.get('simple'):
        msg = f"{VAR_NAME} is not supported for simple conversion"
        print_message(msg)
        return

    msg = 'Starting {name}'.format(name=__name__)
    logging.info(msg)

    meshFileName = infiles['MPAS_mesh']
    mappingFileName = infiles['MPAS_map']
    timeSeriesFiles = infiles['MPASSI']

    dsMesh = xarray.open_dataset(meshFileName, mask_and_scale=False)
    cellMask2D, _ = mpas.get_cell_masks(dsMesh)

    variableList = ['timeMonthly_avg_icePresent', 'xtime_startMonthly',
                    'xtime_endMonthly']

    ds = xarray.Dataset()
    with mpas.open_mfdataset(timeSeriesFiles, variableList) as dsIn:
        ds[VAR_NAME] = dsIn.timeMonthly_avg_icePresent
        ds = mpas.add_time(ds, dsIn)
        ds.compute()

    ds = mpas.add_mask(ds, cellMask2D)
    ds.compute()

    ds = mpas.remap(ds, mappingFileName)

    mpas.setup_cmor(VAR_NAME, tables, user_input_path, component='seaice')

    # create axes
    axes = [{'table_entry': 'time',
             'units': ds.time.units},
            {'table_entry': 'latitude',
             'units': 'degrees_north',
             'coord_vals': ds.lat.values,
             'cell_bounds': ds.lat_bnds.values},
            {'table_entry': 'longitude',
             'units': 'degrees_east',
             'coord_vals': ds.lon.values,
             'cell_bounds': ds.lon_bnds.values}]

    try:
        mpas.write_cmor(axes, ds, VAR_NAME, VAR_UNITS)
    except Exception:
        return ""
    return VAR_NAME
