import os
import ee
import time
import sys
from datetime import datetime
sys.path.append("..") # Adds higher directory to python modules path
from utils import utils
from scripts import gdrive
from utils import parameters as pm

#initialize earth engine
ee.Initialize()

def get_alerts_dates(date_range, aoi_io, asset, band):
    """return the alerts included between the two dates of date_range "band" must be a date in the proleptic Gregorian calendar (number of days since 01/01/01)"""
    
    # get the aoi 
    aoi = aoi_io.get_aoi_ee()
    
    # get the alert asset
    all_alerts = ee.ImageCollection(asset)
        
    # clip the alert dates
    dates = all_alerts.select(band).filterBounds(aoi).mosaic()
    
    # extract julian dates
    start = datetime.strptime(date_range[0], '%Y-%m-%d').toordinal()
    end = datetime.strptime(date_range[1], '%Y-%m-%d').toordinal()
    
    # masked all the images that are not between the limits dates
    date_masked = dates.updateMask(dates.gt(start).And(dates.lt(end)))
    
    return date_masked    

def get_alerts(date_masked, aoi_io, asset, band):
    """ get the alerts from the user asset
    
    Args:
        aoi_name (str): Id of the Aoi to retreive the alerts
        date_masked (ee.Image): the image of the date filter with the given date range
        band (str): the name of the band to retreive (must a a binary band with 1 for alerts)
        
    Returns:
        alerts (ee.FeatureCollection): the alert clipped on the AOI
    """
    
    # get the aoi 
    aoi = aoi_io.get_aoi_ee()
    
    # get the alert asset
    all_alerts = ee.ImageCollection(asset)
    
    # clip the alerts 
    alerts = all_alerts.select(band).filterBounds(aoi).mosaic()
    
    # use the mask of the date alerts 
    alerts = alerts.updateMask(date_masked.mask())
    
    return alerts       
    