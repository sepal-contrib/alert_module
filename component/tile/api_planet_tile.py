import json
import math
from datetime import datetime, timedelta

from sepal_ui import sepalwidgets as sw
from traitlets import Bool
from shapely_geojson import dumps
from shapely.geometry import box
from ipyleaflet import TileLayer
import pandas as pd

from component import widget as cw
from component.message import cm
from component import scripts as cs
from component import parameter as cp


class APIPlanetTile(sw.Card):
    """
    A card to select information from the Planet API
    """

    buffer = None
    "the buffer geometry as a geoseries"

    current_date = None
    "the date saved as a datetime object"

    layers = None
    "list: the list of the currently displayed planet layers"

    def __init__(self, alert_model, map_, planet_model):

        # get the planet model
        self.model = planet_model

        # add an alert to display warning to the user
        self.alert = sw.Alert().show()

        # listent to the alert model
        self.alert_model = alert_model

        # get the map as a member
        self.map = map_

        # init the layer list
        self.layers = []

        # create the control widgets
        self.w_prev_month = cw.MapBtn(
            "mdi-chevron-double-left", class_="ma-0", attributes={"increm": -20}
        )
        self.w_prev_day = cw.MapBtn(
            "mdi-chevron-left", class_="ma-0", attributes={"increm": -1}
        )
        self.w_now = cw.MapBtn("far fa-circle", class_="ma-0", attributes=None)
        self.w_next_day = cw.MapBtn(
            "mdi-chevron-right", class_="ma-0", attributes={"increm": 1}
        )
        self.w_next_month = cw.MapBtn(
            "mdi-chevron-double-right", class_="ma-0", attributes={"increm": 20}
        )
        self.w_date = sw.TextField(
            label=cm.view.planet.date.label,
            v_model=None,
            dense=True,
            class_="ml-1 mr-1",
            readonly=True,
        )

        # aggregate the btns
        btn_list = sw.ItemGroup(
            class_="mr-1 ml-1 v-btn-toggle",
            children=[
                self.w_prev_month,
                self.w_prev_day,
                self.w_now,
                self.w_next_day,
                self.w_next_month,
            ],
        )

        # create a row with all the action widgets
        row = sw.Row(align="center", class_="ma-1", children=[btn_list, self.w_date])

        # create the planet control widgets
        super().__init__(
            class_="pa-2",
            children=[row, self.alert],
            viz=False,
            max_height="80vh",
            max_width="80vw",
        )

        # add javascript event
        self.alert_model.observe(self._toggle_widget, "valid_key")
        self.alert_model.observe(self.load_data, "current_id")
        self.w_prev_month.on_event("click", self._month)
        self.w_prev_day.on_event("click", self._day)
        self.w_now.on_event("click", self._now)
        self.w_next_day.on_event("click", self._day)
        self.w_next_month.on_event("click", self._month)
        self.w_date.observe(self.update_image, "v_model")

    def update_image(self, change):

        # switch off the alert
        self.alert.reset()

        # remove any existing image
        for l in self.layers:
            self.map.remove_layer(l)
        self.layers = []

        # if nothing is selected exit immediately
        if self.w_date.v_model is None:
            return

        # build the start and end date ased on the planet parameters
        start = timedelta(days=-self.alert_model.days_before)
        end = timedelta(days=self.alert_model.days_after)

        # retreive the layer from planet
        items = self.model.get_items(
            self.buffer,
            self.current_day + start,
            self.current_day + end,
            self.alert_model.cloud_cover,
        )

        len(items) > 0 or self.alert.add_msg(cm.planet.no_image, "warning")

        for i, e in enumerate(items):
            date = pd.to_datetime(e["properties"]["acquired"]).strftime("%Y-%m-%d")
            item_type = e["properties"]["item_type"]
            id_ = e["id"]
            name = f"{item_type} {date} ({i})"
            self.map.add_layer(
                TileLayer(
                    url=cp.planet_tile_url.format(
                        item_type, id_, self.model.session._client.auth.value
                    ),
                    name=name,
                    attribution="Imagery © Planet Labs Inc.",
                )
            )
            self.layers.append(name)

        return

    def _toggle_widget(self, change):
        """
        change visibility and displayed information based on the API status
        Only used to close the widget if the value were displayed before the
        deactivation of the API key
        """

        if change["new"] is False:
            self.disable()
            self.hide()

        return

    def unable(self):
        """unable the whole widget"""

        self.w_prev_month.disabled = False
        self.w_prev_day.disabled = False
        self.w_now.disabled = False
        self.w_next_day.disabled = False
        self.w_next_month.disabled = False
        self.w_date.disabled = False

        return self

    def disable(self):
        """disable the whole widget"""

        self.w_prev_month.disabled = True
        self.w_prev_day.disabled = True
        self.w_now.disabled = True
        self.w_next_day.disabled = True
        self.w_next_month.disabled = True
        self.w_date.disabled = True

        return self

    def load_data(self, change):
        """
        load the available image date for the custom feature
        """

        # exit straigh away if an API key is not validated
        if self.alert_model.valid_key is False:
            return

        # unable the widget
        self.unable()

        # reset date values
        # to triger a reload if we change point without changing date
        self.w_date.v_model = None

        if change["new"] is None:
            self.disable()
            self.hide()
            return

        # extract the geometry
        feat = self.alert_model.gdf.loc[[change["new"]]]

        # buffer around the feature in 3857
        feat = feat.to_crs("EPSG:3857")
        feat.geometry = [box(*feat.geometry.buffer(200, cap_style=3).total_bounds)]
        feat = feat.to_crs("EPSG:4326").squeeze()

        # create a buffer geometry
        self.buffer = feat.geometry.__geo_interface__

        # show the widget
        self.show()

        # go to the now item
        self.w_now.fire_event("click", None)

        return

    def _now(self, widget, event, data):
        """change the date to the date of the current alert"""

        # extract the day as a date from the alert_model
        julian, year = math.modf(
            self.alert_model.gdf.at[(self.alert_model.current_id), "date"]
        )
        julian = int(julian * 1000)
        self.current_day = datetime(int(year), 1, 1) + timedelta(days=julian - 1)

        # fill the w_date Textfield to trigger layer update
        self.w_date.v_model = self.current_day.strftime("%Y-%m-%d")

        return

    def _day(self, widget, event, data):
        """
        increment of the specified number of days based on the icrem attribute of the widget
        """

        # set the current date
        self.current_day += timedelta(days=widget.attributes["increm"])

        # fill the w_date Textfield to trigger layer update
        self.w_date.v_model = self.current_day.strftime("%Y-%m-%d")

        return

    def _month(self, widget, event, data):
        """
        increment of the specified number of month based on the icrem attribute of the widget
        """

        # get if we move in the future or the past
        days = widget.attributes["increm"]

        # change month
        day = self.current_day.replace(day=15) + timedelta(days=days)

        # set back the day of month
        dom = 28 if day.month == 2 else self.current_day.day
        day = day.replace(day=dom)

        # set the current date
        self.current_day = day

        # fill the w_date Textfield to trigger layer update
        self.w_date.v_model = self.current_day.strftime("%Y-%m-%d")

        return
