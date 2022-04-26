from datetime import date, datetime
import ee

from component import parameter as cp
from component.message import cm

from .utils import to_date


def get_alerts_clump(alerts, aoi):
    """
    Transform the Image into a featureCollection of agregated alert
    Import it into SEPAL as a GeoJson dict.

    Args:
        alerts (ee.Image): the refactored alerts with an adapted masked to the requested dates
        aoi (ee.FeatureCollection): the featureCollection of the selected AOI

    Return:
        (dict): a geojson dict
    """

    # connectedComponent will analysie all pixels, masked included so it's important
    # to cut the image before starting the object based analysis.
    # clip is not sufficient as it doesn't change the footprint of the image
    alerts = alerts.clipToBoundsAndScale(
        geometry=aoi.geometry(),
        scale=30,
    )

    # Uniquely label the alert image objects.
    object_id = alerts.connectedComponents(
        connectedness=ee.Kernel.square(1), maxSize=1024  # 8 neighbors
    )

    # Compute the number of pixels in each object defined by the "labels" band.
    object_size = (
        object_id.select("labels")
        .connectedPixelCount(eightConnected=True, maxSize=1024)
        .rename("nb_pixel")
    )

    image = object_id.addBands(object_size.select("nb_pixel"))

    # reduce to vector
    alert_collection = image.reduceToVectors(
        reducer=ee.Reducer.min(),  # confirmed are 1, and potential 2
        scale=20,  # force scale < nominalScale to obtain correct results
        eightConnected=True,
        bestEffort=True,
        labelProperty="labels",
        geometry=aoi.geometry(),
    )

    return alert_collection


def get_alerts(collection, start, end, aoi, asset):
    """
    get the alerts restricted to the aoi and the specified dates.
    The Returned images will embed mandatory and optional bands:
    madatory:
        "alert": the alert value 1 for alerts,2 for potential, 0 for no_alerts
        "date": YYYY.julian_day

    Args:
        collection (str): the collection name
        start (str): the start of the analysis (YYYY-MM-DD)
        end (str): the end day of the analysis (YYYY-MM-DD)
        aoi (ee.FeatureCollection): the selected aoi
        asset (str): the asset Id of the Image

    Returns:
        (ee.Image) the alert Image
    """

    if collection == "GLAD-L":
        alerts = _from_glad_l(start, end, aoi)
    elif collection == "RADD":
        alerts = _from_radd(start, end, aoi)
    elif collection == "NRT":
        alerts = _from_nrt(aoi, asset)
    elif collection == "GLAD-S":
        alerts = _from_glad_s(start, end, aoi)
    elif collection == "CUSUM":
        alerts = _from_cusum(aoi, asset)
    else:
        raise Exception(cm.alert.wrong_collection.format(collection))

    return alerts


def _from_glad_l(start, end, aoi):
    """reformat the glad alerts to fit the module expectation"""

    # glad is not compatible with multi year analysis so we cut the dataset into
    # yearly pieces and merge thm together in a second step
    # as it includes multiple dataset I'm not sure I can perform it without a python for loop

    # cut the interval into yearly pieces
    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(end, "%Y-%m-%d")

    periods = [[start, end]]
    tmp = periods.pop()
    while tmp[0].year != tmp[1].year:
        year = tmp[0].year
        periods.append([tmp[0], date(year, 12, 31)])
        periods.append([date(year + 1, 1, 1), tmp[1]])
        tmp = periods.pop()
    periods.append(tmp)

    images = []
    for period in periods:

        year = period[0].year
        start = period[0].timetuple().tm_yday
        end = period[1].timetuple().tm_yday

        if year < cp.alert_drivers["GLAD-L"]["last_updated"]:
            source = f"projects/glad/alert/{year}final"
        else:
            source = "projects/glad/alert/UpdResult"

        # create the composit band alert_date.
        # cannot use the alertDateXX band directly because
        # they are not all casted to the same type
        alerts = (
            ee.ImageCollection(source)
            .map(lambda image: image.uint16())
            .filterBounds(aoi)
            .mosaic()
            .clip(aoi)
        )
        alerts = alerts.updateMask(
            alerts.select(f"alertDate{year%100}")
            .gt(start)
            .And(alerts.select(f"alertDate{year%100}").lt(end))
        )

        # create a unique alert band
        alert_band = (
            alerts.select(f"conf{year%100}")
            .remap([0, 1, 2, 3], [0, 0, 2, 1])
            .rename("alert")
        )

        # change the date format
        date_band = (
            alerts.select(f"alertDate{year%100}")
            .divide(1000)
            .add(ee.Image(year))
            .rename("date")
        )

        # create the composite
        composite = (
            alerts.select(["obsCount", "obsDate"])
            .addBands(date_band)
            .addBands(alert_band)
        )

        images += [composite]

    all_alerts = ee.ImageCollection.fromImages(images).mosaic()

    return all_alerts


def _from_radd(start, end, aoi):
    """reformat the radd alerts to fit the module expectation"""

    # extract dates from parameters
    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(end, "%Y-%m-%d")

    # select the alerts and mosaic them as image
    source = "projects/radar-wur/raddalert/v1"
    alerts = (
        ee.ImageCollection(source)
        .filterBounds(aoi)
        .filterMetadata("layer", "contains", "alert")
        .mosaic()
        .uint16()
    )

    # filter the alerts dates
    # extract julian dates ()
    start = int(start.strftime("%y%j"))
    end = int(end.strftime("%y%j"))

    # masked all the images that are not between the limits dates
    alerts = alerts.updateMask(
        alerts.select("Date").gt(start).And(alerts.select("Date").lt(end))
    )

    # create a unique alert band
    alert_band = (
        alerts.select("Alert").remap([0, 1, 2, 3], [0, 0, 2, 1]).rename("alert")
    )

    # change the date format
    date_band = alerts.select("Date").divide(1000).add(2000).rename("date")

    # create the composit image
    all_alerts = alert_band.addBands(date_band)

    return all_alerts


def _from_nrt(aoi, asset):
    "reformat andreas alert sytem to be compatible with the rest of the apps"

    # read the image
    alerts = ee.Image(asset)

    # create a alert mask
    mask = alerts.select("detection_count").neq(0)

    # create a unique alert band
    # only confirmed alerts are taken into account
    # we split confirmed from potential by looking at the number of observations
    alert_band = (
        alerts.select("detection_count").updateMask(mask).rename("alert").uint16()
    )
    alert_band = alert_band.where(alert_band.gte(1).And(alert_band.lt(3)), 2).where(
        alert_band.gte(3), 1
    )

    # create a unique date band
    date_band = alerts.select("first_detection_date").mask(mask).rename("date")

    # create the composit image
    all_alerts = alert_band.addBands(date_band)

    return all_alerts


def _from_glad_s(start, end, aoi):
    """reformat the glad-s alerts to fit the module expectation"""

    # extract dates from parameters
    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(end, "%Y-%m-%d")

    # the sources are now stored in a folder like system
    init = "projects/glad/S2alert"

    # select the alerts and mosaic them as image
    alert_band = ee.Image(init + "/alert").selfMask().uint16().rename("alert")
    date_band = ee.Image(init + "/obsDate").selfMask().rename("date")

    # alerts are stored in int : number of days since 2018-12-31
    origin = datetime.strptime("2018-12-31", "%Y-%m-%d")
    start = (start - origin).days
    end = (end - origin).days
    date_band = date_band.updateMask(date_band.gt(start).And(date_band.lt(end)))

    # remap the alerts and mask the alerts
    alert_band = (
        alert_band.remap([0, 1, 2, 3, 4], [0, 2, 2, 1, 1]).updateMask(date_band.mask())
    ).rename("alert")

    # change the date format
    date_band = to_date(date_band).rename("date")

    # create the composit image
    all_alerts = alert_band.addBands(date_band)

    return all_alerts


def _from_cusum(aoi, asset):
    "reformat andreas CUSUM alert sytem to be compatible with the rest of the apps"

    # read the image
    alerts = ee.Image(asset)

    # create a unique alert band (2nd band of the output)
    # the alert is considered high confidence if the confidece is above offset
    offset = 0.5
    alert_band = alerts.select(2)
    alert_band = (
        alert_band.where(alert_band.gte(offset), 1)
        .where(alert_band.lt(offset), 2)
        .uint16()
        .rename("alert")
    )

    # create a unique date band
    date_band = alerts.select(0).rename("date")

    # create the composit image
    all_alerts = alert_band.addBands(date_band)

    return all_alerts
