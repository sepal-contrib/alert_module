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

def get_alerts_dates(aoi_name, date_range, asset, band):
    """return the alerts included between the two dates of date_range "band" must be a date in the proleptic Gregorian calendar (number of days since 01/01/01)"""
    
    all_alerts = ee.ImageCollection(asset)
        
    #clip the alert dates
    dates = all_alerts.select(band).mosaic().clip(aoi)

    #masked all the images that are not between the limits dates
    
    #extract julian dates
    start = datetime.strptime(date_range[0], '%Y-%m-%d').toordinal()
    end = datetime.strptime(date_range[1], '%Y-%m-%d').toordinal()
    
    date_masked = dates.updateMask(dates.gt(start).And(dates.lt(end)))
    
    return date_masked    

def get_alerts(aoi_name, date_masked, asset, band):
    """ get the alerts from the user asset
    
    Args:
        aoi_name (str): Id of the Aoi to retreive the alerts
        date_masked (ee.Image): the image of the date filter with the given date range
        band (str): the name of the band to retreive (must a a binary band with 1 for alerts)
        
    Returns:
        alerts (ee.FeatureCollection): the alert clipped on the AOI
    """
    
    aoi = ee.FeatureCollection(aoi_name)
    
    all_alerts = ee.ImageCollection(asset)
    
        
    alerts = all_alerts.select(band).mosaic().clip(aoi);
    
    #use the mask of the date alerts 
    alerts = alerts.updateMask(date_masked.mask())
    
    return alerts       
    