from sepal_ui import color as sc

alert_style = {  # default styling of the layer
    "stroke": True,
    "color": sc.error,
    "weight": 2,
    "opacity": 1,
    "fill": True,
    "fillColor": sc.error,
    "fillOpacity": 0,
}

current_alert_style = {  # current alert styling
    "stroke": True,
    "color": sc.warning,
    "weight": 5,  # same weight as hover to hide the general layer
    "opacity": 1,
    "fill": True,  # to avoid unwanted click on the underlying alert
    "fillColor": sc.warning,
    "fillOpacity": 0,
}

edit_style = {  # style of the edited geometry
    "stroke": True,
    "color": "#79b1c9",
    "weight": 4,
    "opacity": 0.5,
    "fill": True,
    "fillColor": None,
    "fillOpacity": 0.2,
    "clickable": True,
}

planet_viz = {"min": 64, "max": 5454, "gamma": 1.8}  # I let the driver decide the bands
