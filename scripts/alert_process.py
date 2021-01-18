import os
from datetime import datetime
import glob
import time
from pathlib import Path

import rasterio as rio
from rasterio.merge import merge

from scripts import alert_driver as ad
from scripts import glad_import
from scripts import gee_import
from scripts import gdrive
from utils import messages as ms
from utils import utils

def get_alerts(aoi_io, io, output):
    
    if io.alert_type == ad.available_drivers[0]: # gee assets
        return get_gee_assets(aoi_io, io, output)
    
    if io.alert_type == ad.available_drivers[1]: # local files 
        return get_local_alerts(aoi_io, io, output)
    
    if io.alert_type == ad.available_drivers[2]: # glad alerts
        return get_glad_alerts(aoi_io, io, output)
    
    # if I'm here it means that the io_alert_type is not define 
    output.add_live_msg(io.alert_type, 'error')
    return (None, None)

def get_glad_alerts(aoi_io, io, output):
    
    # verify useful inputs 
    if not output.check_input(io.start): return (None, None)
    if not output.check_input(io.end): return (None, None)
    
    #convert to dates
    start = datetime.strptime(io.start, '%Y-%m-%d')
    end = datetime.strptime(io.end, '%Y-%m-%d')
    
    # check that the year is not prior to 2017
    if start.year < 2017:
        output.add_live_msg(ms.TOO_EARLY, 'error')
        return (None, None)
    
    # verify the dates are in the same year
    if start.year != end.year:
        output.add_live_msg(ms.WRONG_YEAR, 'error')
        return (None, None)
    
    year = start.year
    
    # filename 
    aoi_name = aoi_io.get_aoi_name()
    filename = aoi_name + f'_{io.start}_{io.end}_glad_alerts'
    
    # check if the file exist 
    result_dir = utils.create_result_folder(aoi_io)
    
    basename = f'{result_dir}{aoi_name}_{io.start}_{io.end}_glad'
    alert_date_tmp_map = f'{basename}_tmp_date.tif'
    alert_date_map     = f'{basename}_date.tif'
    alert_tmp_map      = f'{basename}_tmp_map.tif'
    alert_raw_map      = f'{basename}_raw_map.tif'
    alert_map          = f'{basename}_map.tif'
    
    if os.path.isfile(alert_tmp_map) or os.path.isfile(alert_map):
        output.add_live_msg(ms.ALREADY_DONE, 'success')
        return (alert_date_tmp_map, alert_tmp_map)
    
    drive_handler = gdrive.gdrive()
    
    # check for the julian day task 
    filename_date = f'{filename}_dates'
    alerts_date = glad_import.get_alerts_dates(aoi_io, year, [io.start, io.end])
    download = drive_handler.download_to_disk(filename_date, alerts_date, aoi_io, output)
    
    # reteive alert date masked with date range 
    filename_map = f'{filename}_map'
    alerts = glad_import.get_alerts(aoi_io, year, alerts_date)
    download = drive_handler.download_to_disk(filename_map, alerts, aoi_io, output)
    
    # wait for completion 
    # I assume that there is 2 or 0 file to launch 
    # if one of the 2 process have been launch individually it will crash
    if download:
        utils.wait_for_completion([filename_map, filename_date], output)
        output.add_live_msg(ms.TASK_COMPLETED.format(filename_map), 'success') 
    
    # merge and compress them 
    digest_tiles(aoi_io, filename_date, result_dir, output, alert_date_tmp_map)
    digest_tiles(aoi_io, filename_map, result_dir, output, alert_tmp_map)
    
    # remove the files from gdrive 
    drive_handler.delete_files(drive_handler.get_files(filename_date))
    drive_handler.delete_files(drive_handler.get_files(filename_map))
    
    output.add_live_msg(ms.COMPUTAION_COMPLETED, 'success')
    
    # return the obtained files
    return (alert_date_tmp_map, alert_tmp_map)
    
    
def get_gee_assets(aoi_io, io, output):
    
    # verify useful inputs 
    if not output.check_input(io.start): return (None, None)
    if not output.check_input(io.end): return (None, None)
    if not output.check_input(io.date_asset): return (None, None)
    if not output.check_input(io.alert_asset): return (None, None)
    if not output.check_input(io.asset_date_band): return (None, None)
    if not output.check_input(io.asset_alerts_band): return (None, None)
    
    # check that the asset exist 
    
    # filename 
    asset_name = Path(io.alert_asset).stem
    aoi_name = aoi_io.get_aoi_name()
    filename = f'{aoi_name}_{io.start}_{io.end}_{asset_name}_alerts'
    
    # check if the file exist 
    result_dir = utils.create_result_folder(aoi_io)
    
    basename = f'{result_dir}{aoi_name}_{io.start}_{io.end}_{asset_name}'
    alert_date_tmp_map = f'{basename}_tmp_date.tif'
    alert_date_map     = f'{basename}_date.tif'
    alert_tmp_map      = f'{basename}_tmp_map.tif'
    alert_map          = f'{basename}_map.tif'
    
    if os.path.isfile(alert_tmp_map):
        output.add_live_msg(ms.ALREADY_DONE, 'success')
        return (alert_date_tmp_map, alert_tmp_map)
    
    drive_handler = gdrive.gdrive()
    
    # mask the appropriate alerts 
    filename_date = f'{filename}_dates'
    alerts_date = gee_import.get_alerts_dates([io.start, io.end], io.date_asset, io.asset_date_band)
    download = drive_handler.download_to_disk(filename_date, alerts_date.unmask(0), aoi_io, output)
    
    # reteive alert date masked with date range 
    filename_map = f'{filename}_map'
    alerts = gee_import.get_alerts(alerts_date, io.alert_asset, io.asset_alerts_band)
    download = drive_handler.download_to_disk(filename_map, alerts.unmask(0), aoi_io, output)
    
    # wait for completion 
    # I assume that there is 2 or 0 file to launch 
    # if one of the 2 process have been launch individually it will crash
    if download:
        utils.wait_for_completion([filename_map, filename_date], output)
        output.add_live_msg(ms.TASK_COMPLETED.format(filename_map), 'success') 
    
    # merge and compress them 
    digest_tiles(aoi_io, filename_date, result_dir, output, alert_date_tmp_map)
    digest_tiles(aoi_io, filename_map, result_dir, output, alert_tmp_map)
    
    # remove the files from gdrive 
    drive_handler.delete_files(drive_handler.get_files(filename_date))
    drive_handler.delete_files(drive_handler.get_files(filename_map))
    
    output.add_live_msg(ms.COMPUTAION_COMPLETED, 'success')
    
    # return the obtained files
    return (alert_date_tmp_map, alert_tmp_map)


def get_local_alerts(aoi_io, io, output):
    
    if not output.check_input(io.start): return (None, None)
    if not output.check_input(io.start): return (None, None)
    if not output.check_input(io.date_file): return (None, None)
    if not output.check_input(io.alert_file): return (None, None)
    
    # check that the file exist 
    if not os.path.isfile(io.date_file): return (None, None)
    if not os.path.isfile(io.alert_file): return (None, None)
    
    #filename 
    alert_name = Path(io.alert_file).stem
    aoi_name = aoi_io.get_aoi_name()
    filename = f'{aoi_name}_{io.start}_{io.end}_{alert_name}_alerts'
    
    #check if the file exist 
    result_dir = utils.create_result_folder(aoi_io)
    
    basename = f'{result_dir}{aoi_name}_{io.start}_{io.end}_{alert_name}' 
    alert_date_map     = f'{basename}_tmp_date.tif'
    alert_map          = f'{basename}_tmp_map.tif'
    
    if os.path.isfile(alert_map):
        output.add_live_msg(ms.ALREADY_DONE, 'success')
        return (alert_date_map, alert_map)
    
    #mask the alert dates 
    start = datetime.strptime(io.start, '%Y-%m-%d').toordinal()
    end = datetime.strptime(io.end, '%Y-%m-%d').toordinal()
    
    with rio.open(io.date_file) as src:
        
        raw_data = src.read()
        out_meta = scr.meta.copy()
        data = ((raw_data >= start)*(raw_data <= end)) * raw_data
        
        with rio.open(alert_date_map, 'w', **out_meta) as dest:
            dest.write(data)
    
    #filter the alerts 
    with rio.open(alert_date_map) as date, rio.open(io.alert_file) as alert:
        
        date_data = date.read()
        alert_data = alert.read() 
        
        # I assume that they both have the same extend, res, and transform
        out_meta = date.meta.copy()
        out_meta.update(
            dtype=rasterio.uint8,
            compress='lzw'
        )
        
        data = (date_data > 0) * alert_data
        
        with rio.open(alert_map) as dest:
            dest.write(data)
    
    output.add_live_msg(ms.COMPUTAION_COMPLETED, 'success')
    
    # return the obtained files
    return (alert_date_map, alert_map)

def digest_tiles(aoi_io, filename, result_dir, output, tmp_file):
    
    drive_handler = gdrive.gdrive()
    files = drive_handler.get_files(filename)
    drive_handler.download_files(files, result_dir)
    
    pathname = f'{filename}*.tif'
    
    files = [file for file in glob.glob(result_dir + pathname)]
        
    #run the merge process
    output.add_live_msg(ms.MERGE_TILE)
    time.sleep(2)
    
    #manual open and close because I don't know how many file there are
    sources = [rio.open(file) for file in files]

    data, output_transform = merge(sources)
    
    out_meta = sources[0].meta.copy()    
    out_meta.update(
        driver    = "GTiff",
        height    =  data.shape[1],
        width     =  data.shape[2],
        transform = output_transform,
        compress  = 'lzw'
    )
    
    with rio.open(tmp_file, "w", **out_meta) as dest:
        dest.write(data)
    
    # manually close the files
    [src.close() for src in sources]
    
    # delete local files
    [os.remove(file) for file in files]
    
    return
    