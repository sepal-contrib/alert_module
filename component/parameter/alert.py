from component.message import cm

alert_drivers = {
    "GLAD-L": {
        "available_years": range(2017, 2022),
        "last_updated": 2020,
        "asset": "projects/glad/alert/UpdResult",
    },
    "RADD": {
        "available_years": range(2019, 2023),
        "asset": "projects/radar-wur/raddalert/v1",
    },
    "NRT": {},
    "GLAD-S": {
        "available_years": range(2018, 2023),
        "asset": "projects/glad/S2alert/alert",
    },
    "CUSUM": {},
}

# the amont of days to look for in the past
time_delta = [
    {"text": cm.parameter.time_delta.day, "value": 1},
    {"text": cm.parameter.time_delta.week, "value": 7},
    {"text": cm.parameter.time_delta.month, "value": 31},
]
