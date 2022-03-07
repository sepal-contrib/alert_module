from component.message import cm

alert_drivers = {
    "GLAD": {"available_years": range(2017, 2022), "last_updated": 2020},
    "RADD": {"available_years": range(2019, 2023)},
    "NRT": {},
}

# the amont of days to look for in the past
time_delta = [
    {"text": cm.parameter.time_delta.day, "value": 1},
    {"text": cm.parameter.time_delta.week, "value": 7},
    {"text": cm.parameter.time_delta.month, "value": 31},
]
