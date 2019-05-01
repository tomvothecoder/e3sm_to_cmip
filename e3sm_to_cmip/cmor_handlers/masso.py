
"""
compute Sea Water Mass, masso
"""

from __future__ import absolute_import, division, print_function

import xarray
import logging

from e3sm_to_cmip import mpas

# 'MPAS' as a placeholder for raw variables needed
RAW_VARIABLES = ['MPASO', 'MPASO_namelist', 'MPAS_mesh']

# output variable name
VAR_NAME = 'masso'
VAR_UNITS = 'kg'
TABLE = 'CMIP6_Omon.json'


def handle(infiles, tables, user_input_path, **kwargs):
    """
    Transform MPASO timeMonthly_avg_layerThickness into CMIP.masso

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

    namelistFileName = infiles['MPASO_namelist']
    meshFileName = infiles['MPAS_mesh']
    timeSeriesFiles = infiles['MPASO']

    namelist = mpas.convert_namelist_to_dict(namelistFileName)
    config_density0 = float(namelist['config_density0'])

    dsMesh = xarray.open_dataset(meshFileName, mask_and_scale=False)
    _, cellMask3D = mpas.get_cell_masks(dsMesh)

    variableList = ['timeMonthly_avg_layerThickness', 'xtime_startMonthly',
                    'xtime_endMonthly']

    ds = xarray.Dataset()
    with mpas.open_mfdataset(timeSeriesFiles, variableList) as dsIn:
        ds[VAR_NAME] = (config_density0 *
                        dsIn.timeMonthly_avg_layerThickness.where(cellMask3D) *
                        dsMesh.areaCell).sum(dim=['nVertLevels', 'nCells'])
        ds = mpas.add_time(ds, dsIn)
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