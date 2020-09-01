from scripts import alert_driver as ad
from datetime import datetime
from utils import messages as ms
import os
from scripts import glad_import
from scripts import gee_import
from sepal_ui import gdal as sgdal
from utils import utils
from scripts import gdrive
import glob
import time
import gdal

def get_alerts(aoi_io, io, output):
    
    if io.alert_type == ad.available_drivers[0]: # gee assets
        return get_gee_assets(aoi_io, io, output)
    
    if io.alert_type == ad.available_drivers[1]: # local files 
        return get_local_alerts(aoi_io, io, output)
    
    if io.alert_type == ad.available_drivers[2]: # glad alerts
        return get_glad_alerts(aoi_io, io, output)
    
    # if I'm here it means that the io_alert_type is not define 
    output.add_live_msg(io.alert_type, 'error')
    #output.add_live_msg(ms.WRONG_DRIVER, 'error')
    return (None, None)

def get_glad_alerts(aoi_io, io, output):
    
    #verify useful inputs 
    if not output.check_input(io.start): return (None, None)
    if not output.check_input(io.end): return (None, None)
    
    #convert to dates
    start = datetime.strptime(io.start, '%Y-%m-%d')
    end = datetime.strptime(io.end, '%Y-%m-%d')
    
    # verify the dates are in the same year
    if start.year != end.year:
        output.add_live_msg(ms.WRONG_YEAR, 'error')
        return (None, None)
    year = start.year
    
    #filename 
    aoi_name = os.path.split(aoi_io.assetId)[1].replace('aoi_','')
    filename = aoi_name + '_{0}_{1}_glad_alerts'.format(io.start, io.end)
    
    #check if the file exist 
    alert_dir = utils.create_result_folder(aoi_name)
    
    basename = alert_dir + aoi_name + '_' + io.start + '_' + io.end 
    alert_date_tmp_map = basename + '_tmp_glad_date.tif'
    alert_date_map     = basename + '_glad_date.tif'
    alert_tmp_map      = basename + '_tmp_glad_map.tif'
    alert_map          = basename + '_glad_map.tif'
    
    if os.path.isfile(alert_map):
        output.add_live_msg(ms.ALREADY_DONE, 'success')
        return (alert_date_map, alert_map)
    
    drive_handler = gdrive.gdrive()
    
    #check for the julian day task 
    filename_date = filename + '_dates'
    alerts_date = glad_import.get_alerts_dates(aoi_io.assetId, year, [io.start, io.end])
    download = drive_handler.download_to_disk(filename_date, alerts_date, aoi_io.assetId, output)
    
    #reteive alert date masked with date range 
    filename_map = filename + '_map'
    alerts = glad_import.get_alerts(aoi_io.assetId, year, alerts_date)
    download = drive_handler.download_to_disk(filename_map, alerts, aoi_io.assetId, output)
    
    #wait for completion 
    # I assume that there is 2 or 0 file to launch 
    # if one of the 2 process have been launch individually it will crash
    if download:
        utils.wait_for_completion([filename_map, filename_date], output)
        output.add_live_msg(ms.TASK_COMPLETED.format(filename_map), 'success') 
    
    # merge and compress them 
    digest_tiles(filename_date, alert_dir, output, alert_date_tmp_map, alert_date_map)
    digest_tiles(filename_map, alert_dir, output, alert_tmp_map, alert_map)
    
    # return the obtained files
    return (alert_date_map, alert_map)
    
    
def get_gee_assets(aoi_io, io, output):
    
    #verify useful inputs 
    if not output.check_input(io.start): return (None, None)
    if not output.check_input(io.end): return (None, None)
    if not output.check_input(io.date_asset): return (None, None)
    if not output.check_input(io.alert_asset): return (None, None)
    if not output.check_input(io.asset_date_band): return (None, None)
    if not output.check_input(io.asset_alerts_band): return (None, None)
    
    # check that the asset exist 
    
    #filename 
    aoi_name = os.path.split(aoi_io.assetId)[1].replace('aoi_','')
    filename = aoi_name + '_{0}_{1}_gee_alerts'.format(io.start, io.end)
    
    #check if the file exist 
    alert_dir = utils.create_result_folder(aoi_name)
    
    basename = alert_dir + aoi_name + '_' + io.start + '_' + io.end 
    alert_date_tmp_map = basename + '_tmp_glad_date.tif'
    alert_date_map     = basename + '_glad_date.tif'
    alert_tmp_map      = basename + '_tmp_glad_map.tif'
    alert_map          = basename + '_glad_map.tif'
    
    if os.path.isfile(alert_map):
        output.add_live_msg(ms.ALREADY_DONE, 'success')
        return (alert_date_map, alert_map)
    
    drive_handler = gdrive.gdrive()
    
    
    # mask the appropriate alerts 
    filename_date = filename + '_dates'
    alerts_date = gee_import.get_alerts_dates(aoi_io.assetId, [io.start, io.end], io.date_asset, io.asset_date_band)
    download = drive_handler.download_to_disk(filename_date, alerts_date, aoi_io.assetId, output)
    
    #reteive alert date masked with date range 
    filename_map = filename + '_map'
    alerts = glad_import.get_alerts(aoi_io.assetId, alerts_date, io.alerts_asset, io.asset_alerts_band)
    download = drive_handler.download_to_disk(filename_map, alerts, aoi_io.assetId, output)
    
    #wait for completion 
    # I assume that there is 2 or 0 file to launch 
    # if one of the 2 process have been launch individually it will crash
    if download:
        utils.wait_for_completion([filename_map, filename_date], output)
        output.add_live_msg(ms.TASK_COMPLETED.format(filename_map), 'success') 
    
    # merge and compress them 
    digest_tiles(filename_date, alert_dir, output, alert_date_tmp_map, alert_date_map)
    digest_tiles(filename_map, alert_dir, output, alert_tmp_map, alert_map)
    
    # return the obtained files
    return (alert_date_map, alert_map)


def get_local_alerts(aoi_io, io, output):
    
    if not output.check_input(io.start): return (None, None)
    if not output.check_input(io.start): return (None, None)
    if not output.check_input(io.date_file): return (None, None)
    if not output.check_input(io.alert_file): return (None, None)
    
    # check that the file exist 
    if not os.path.isfile(io.date_file): return (None, None)
    if not os.path.isfile(io.alert_file): return (None, None)
    
    #filename 
    aoi_name = os.path.split(aoi_io.assetId)[1].replace('aoi_','')
    filename = aoi_name + '_{0}_{1}_gee_alerts'.format(io.start, io.end)
    
    #check if the file exist 
    alert_dir = utils.create_result_folder(aoi_name)
    
    basename = alert_dir + aoi_name + '_' + io.start + '_' + io.end 
    alert_date_map     = basename + '_glad_date.tif'
    alert_map          = basename + '_glad_map.tif'
    
    if os.path.isfile(alert_map):
        output.add_live_msg(ms.ALREADY_DONE, 'success')
        return (alert_date_map, alert_map)
    
    #mask the alert dates 
    start = datetime.strptime(date_range[0], '%Y-%m-%d').toordinal()
    end = datetime.strptime(date_range[1], '%Y-%m-%d').toordinal()
    
    
    calc = "(A>={0})*(A<={1})*A".format(start, end)
    sgdal.calc(calc, [io.date_file], alert_date_map, Type_='Byte', co='COMPRESS=LZW')
    
    #filter the alerts 
    calc = "(A>0)*B"
    sgdal.calc(calc, [alert_date_map, io.alert_file], alert_map, Type_='Byte', co='COMPRESS=LZW')
    
    # return the obtained files
    return (alert_date_map, alert_map)

def digest_tiles(filename, alert_dir, output, tmp_file, comp_file):
    
    drive_handler = gdrive.gdrive()
    files = drive_handler.get_files(filename)
    drive_handler.download_files(files, alert_dir)
    
    pathname = filename + "*.tif"
    
    files = [file for file in glob.glob(alert_dir + pathname)]
        
    #run the merge process
    output.add_live_msg(ms.MERGE_TILE)
    time.sleep(2)
    io = sgdal.merge(files, out_filename=tmp_file, v=True, output=output)
    
    #delete local files
    [os.remove(file) for file in files]
    
    #compress raster
    output.add_live_msg(ms.COMPRESS_FILE)
    gdal.Translate(comp_file, tmp_file, creationOptions=['COMPRESS=LZW'])
    os.remove(tmp_file)
    
    return
    
    