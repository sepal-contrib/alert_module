"""
This file will be used as a singleton object to manage connection tot he 
planet API
"""

from datetime import datetime
import re
import requests

from planet import api
from planet.api import filters

from component import parameter as cp
from component.message import cm

url = "https://api.planet.com/auth/v1/experimental/public/my/subscriptions"
subs = None
active = None


def client(api_key):
    """return the client api object"""

    return api.ClientV1(api_key=api_key)


def get_subscription(api_key):
    """load the user subscriptions and throw an error if none are found"""

    resp = requests.get(url, auth=(api_key, ""))
    subscriptions = resp.json()

    if resp.status_code == 200:
        return subscriptions

    return []


def is_active(api_key):
    """check if the key is activated"""

    # get the subs from the api key
    subs = get_subscription(api_key)

    # read the subs
    # it will be empty if no sub are set
    return any([True for s in subs if s["state"] == "active"])


def planet_moasics(mosaic):
    """from a planet mosaic name extract a meaningful short name"""

    if re.compile(cp.regex_monthly).match(mosaic):
        year, start = re.search(cp.regex_monthly, mosaic).groups()
        start = datetime.strptime(start, "%m").strftime("%b")
        res = f"{start} {year}"
    elif re.compile(cp.regex_bianual).match(mosaic):
        year, start, end = re.search(cp.regex_bianual, mosaic).groups()
        start = datetime.strptime(start, "%m").strftime("%b")
        end = datetime.strptime(end, "%m").strftime("%b")
        res = f"{start}-{end} {year}"
    else:
        raise Exception(cm.planet.no_nicfi.format(mosaic))

    return res


def get_planet_items(api_key, aoi, start, end, cloud_cover):
    """
    Request imagery items from the planet API for the requested dates.

    Args:
        api_key (str): the valid api key
        aoi(geojson): the geometry of the alert
        start(datetime.date): the start of the request
        end (datetime.date): the end of the request
        cloud_cover (int): the cloud coverage tolerated

    Return:
        (list): items from the Planet API
    """

    query = filters.and_filter(
        filters.geom_filter(aoi),
        filters.range_filter("cloud_cover", lte=cloud_cover),
        filters.date_range("acquired", gt=start),
        filters.date_range("acquired", lt=end),
    )

    # Skipping REScene because is not orthorrectified and
    # cannot be clipped.
    asset_types = ["PSScene"]

    # build the request
    request = filters.build_search_request(query, asset_types)
    result = client(api_key).quick_search(request)

    # get all the results
    items_pages = []
    for page in result.iter(None):
        items_pages.append(page.get())

    items = [item for page in items_pages for item in page["features"]]

    return items
