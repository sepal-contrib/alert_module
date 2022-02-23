from datetime import date, datetime
import ee

from component import parameter as cp


def get_alerts_clump(alerts, aoi, min_size):
    """
    Transform the Image into a featureCollection of agregated alert
    Import it into SEPAL as a GeoJson dict.

    Args:
        alerts (ee.Image): the refactored alerts with an adapted masked to the requested dates
        aoi (ee.FeatureCollection): the featureCollection of the selected AOI
        min_size (int): the minimal size of the events in ha

    Return:
        (dict): a geojson dict
    """

    # connectedComponent will analysie all pixels, masked included so it's important
    # to cut the image before starting the object based analysis.
    # clip is not sufficient as it doesn't change the footprint of the image
    alerts = alerts.clipToBoundsAndScale(
        geometry=aoi.geometry(),
        scale=30,  # alerts.select('alert').projection().nominalScale().getInfo()
    )

    # Uniquely label the alert image objects.
    object_id = alerts.connectedComponents(
        connectedness=ee.Kernel.square(1), maxSize=1024  # 8 neighbors
    )

    # Compute the number of pixels in each object defined by the "labels" band.
    object_size = object_id.select("labels").connectedPixelCount(
        eightConnected=True, maxSize=1024
    )

    # Multiply pixel area by the number of pixels in an object to calculate
    # the object area. The result is an image where each pixel
    # of an object relates the area of the object in ha.
    pixel_area = ee.Image.pixelArea()
    object_area = object_size.multiply(pixel_area).divide(10000).rename("surface")
    image = object_id.addBands(object_area.select("surface"))

    # reduce to vector
    alert_collection = image.reduceToVectors(
        reducer=ee.Reducer.min(),  # confirmed are 1, and potential 2
        scale=20,  # force scale < nominalScale to obtain correct results
        eightConnected=True,
        bestEffort=True,
        labelProperty="labels",
        geometry=aoi.geometry(),
    )

    # filter and sort the colection by size
    alert_collection = alert_collection.filter(ee.Filter.gte("surface", min_size)).sort(
        "surface", False
    )

    # create 0 index numerotation
    indexes = ee.List(alert_collection.aggregate_array("system:index"))
    ids = ee.List.sequence(1, indexes.size())
    id_by_index = ee.Dictionary.fromLists(indexes, ids)
    alert_collection = alert_collection.map(
        lambda feat: feat.set("id", id_by_index.get(feat.get("system:index")))
    )

    return alert_collection


def get_alerts(collection, start, end, aoi):
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

    Returns:
        (ee.Image) the alert Image
    """

    if collection == "GLAD":
        alerts = _from_glad(start, end, aoi)
    else:
        raise Exception(
            f"{collection} alert collection is not yet included in the tool"
        )

    return alerts


def _from_glad(start, end, aoi):
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

        print(year)
        print(start)
        print(end)

        if year < cp.alert_drivers["GLAD"]["last_updated"]:
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
