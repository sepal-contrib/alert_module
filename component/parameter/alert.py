from datetime import date
from component.message import cm

now = date.today().year

alert_drivers = {
    "GLAD-L": {
        "available_years": range(2017, now + 1),
        "last_updated": 2022,
        "asset": "projects/glad/alert/UpdResult",
    },
    "RADD": {
        "available_years": range(2019, now + 1),
        "asset": "projects/radar-wur/raddalert/v1",
    },
    "NRT": {},
    "GLAD-S": {
        "available_years": range(2018, now + 1),
        "asset": "projects/glad/S2alert/alert",
    },
    "CUSUM": {},
    "SINGLE-DATE": {},
    "RECOVER": {},
    "JJ-FAST": {"available_years": range(2016, now + 1)},
}

# the amont of days to look for in the past
time_delta = [
    {"text": cm.parameter.time_delta.day, "value": 1},
    {"text": cm.parameter.time_delta.week, "value": 7},
    {"text": cm.parameter.time_delta.month, "value": 31},
]
