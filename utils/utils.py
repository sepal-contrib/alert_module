import csv
import ee
import os
from datetime import datetime
import time
import ipyvuetify as v
import glob
from pathlib import Path
import geemap
import string

#initialize earth engine
ee.Initialize()


    


def construct_filename(aoi_io, date_range):
    """return the filename associated with the current task
    
    Args:
        asset_name (str): the ID of the asset
        date_range ([str, str]): the range of date to retreive the GLAD alerts (Y-m-d)
    
    Returns:
        filename (str): the filename to save the Tif files
    """
    aoi_name = aoi_io.get_aoi_name()
    filename = f'{aoi_name}_{ate_range[0]}_{ate_range[1]}_alerts' 
    
    return filename

def init_result_map():
    """initialize a geemap to display the aggregated data"""
    
    # init a map center in 0,0
    m = geemap.Map(
        center=(0, 0),
        zoom=2
    )
    
    # remove layers and controls
    m.clear_layers()
    m.clear_controls()
    
    #use the carto basemap
    m.add_basemap('Esri.WorldImagery')
    
    #add the useful controls 
    m.add_control(geemap.ZoomControl(position='topright'))
    m.add_control(geemap.LayersControl(position='topright'))
    m.add_control(geemap.AttributionControl(position='bottomleft'))
    m.add_control(geemap.ScaleControl(position='bottomleft', imperial=False))

    return m
           

    
      