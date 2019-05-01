
"""
compute Global Average Sea Surface Temperature, tosga
"""
from __future__ import absolute_import, division, print_function

import xarray
import logging

from e3sm_to_cmip import mpas

# 'MPAS' as a placeholder for raw variables needed
RAW_VARIABLES = ['MPASO', 'MPAS_mesh']

# output variable name
VAR_NAME = 'tosga'
VAR_UNITS = 'degC'
TABLE = 'CMIP6_Omon.json'


def handle(infiles, tables, user_input_path, **kwargs):
    """
    Transform MPASO timeMonthly_avg_activeTracers_temperature into CMIP.tosga

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
    msg = 'Starting {name}'.format(name=__name__)
    logging.info(msg)

    meshFileName = infiles['MPAS_mesh']
    timeSeriesFiles = infiles['MPASO']

    dsMesh = xarray.open_dataset(meshFileName, mask_and_scale=False)
    cellMask2D, _ = mpas.get_cell_masks(dsMesh)

    variableList = ['timeMonthly_avg_activeTracers_temperature',
                    'xtime_startMonthly', 'xtime_endMonthly']

    ds = xarray.Dataset()
    with mpas.open_mfdataset(timeSeriesFiles, variableList) as dsIn:
        thetao = dsIn.timeMonthly_avg_activeTracers_temperature
        tos = thetao.isel(nVertLevels=0).squeeze(drop=True).where(cellMask2D)
        areaCell = dsMesh.areaCell.where(cellMask2D)
        ds[VAR_NAME] = ((tos*areaCell).sum(dim='nCells') /
                        areaCell.sum(dim='nCells'))
        ds = mpas.add_time(ds, dsIn)
        ds.compute()
    ds.compute()

    mpas.setup_cmor(VAR_NAME, tables, user_input_path, component='ocean')

    # create axes
    axes = [{'table_entry': 'time',
             'units': ds.time.units}]
    try:
        mpas.write_cmor(axes, ds, VAR_NAME, VAR_UNITS)
    except Exception:
        return ""
    return VAR_NAME