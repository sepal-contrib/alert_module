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

    api.ClientV1(api_key=api_key)


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
