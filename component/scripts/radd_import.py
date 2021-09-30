import time
from datetime import datetime

import ee

# initialize earth engine
ee.Initialize()


def get_alerts_dates(aoi, date_range):
    """return the julian day map of the radd alerts included between the two dates of date_range"""

    # get all the alerts
    all_alerts = ee.ImageCollection("projects/radar-wur/raddalert/v1")

    # clip on the aoi
    dates = (
        all_alerts.select("Date")
        .filterBounds(aoi)
        .filterMetadata("layer", "contains", "alert")
        .mosaic()
        .uint16()
    )

    # extract julian dates ()
    start = int(date_range[0].strftime("%y%j"))
    end = int(date_range[1].strftime("%y%j"))

    # masked all the images that are not between the limits dates
    date_masked = dates.updateMask(dates.gt(start).And(dates.lt(end)))

    return date_masked


def get_alerts(aoi, date_masked):
    """get the alerts from the GLAD project

    Args:
        aoi_name (str): Id of the Aoi to retreive the alerts
        year, (str): year of alerts in format YYYY
        date_masked (ee.Image): the image of the date filter with the given date range

    Returns:
        alerts (ee.FeatureCollection): the Glad alert clipped on the AOI
    """

    # get all the alerts
    all_alerts = ee.ImageCollection("projects/radar-wur/raddalert/v1")

    # clip on the aoi
    alerts = (
        all_alerts.select("Alert")
        .filterBounds(aoi)
        .filterMetadata("layer", "contains", "alert")
        .mosaic()
        .uint16()
    )

    # use the mask of the julian alerts
    alerts = alerts.updateMask(date_masked.mask())

    return alerts
