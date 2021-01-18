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

#messages 
STATUS = "Status : {0}"
    
def wait_for_completion(task_descripsion, output):
    """Wait until the selected process are finished. Display some output information

    Args:
        task_descripsion ([str]) : name of the running tasks
        widget_alert (v.Alert) : alert to display the output messages
    
    Returns: state (str) : final state
    """
    state = 'UNSUBMITTED'
    while not (state == 'COMPLETED' or state =='FAILED'):
        output.add_live_msg(STATUS.format(state))
        time.sleep(5)
                    
        #search for the task in task_list
        for task in task_descripsion:
            current_task = search_task(task)
            state = current_task.state
            if state == 'RUNNING': break
    
    return state

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

def search_task(task_descripsion):
    """Search for the described task in the user Task list return None if nothing is find
    
    Args: 
        task_descripsion (str): the task descripsion
    
    Returns
        task (ee.Task) : return the found task else None
    """
    
    tasks_list = ee.batch.Task.list()
    current_task = None
    for task in tasks_list:
        if task.config['description'] == task_descripsion:
            current_task = task
            break
            
    return current_task

def create_result_folder(aoi_io):
    """Create a folder to download the glad images
   
    Args:
        aoiId(str) : the Id to the asset
    
    Returns:
        glad_dir (str): pathname to the glad_result folder
    """
    aoi = aoi_io.get_aoi_name()
    glad_dir = os.path.join(os.path.expanduser('~'), 'alerts_results') + '/'
        
    pathname = glad_dir + aoi + '/'
    if not os.path.exists(pathname):
        os.makedirs(pathname)
    
    return pathname

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
           

    
      