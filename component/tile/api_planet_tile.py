import json
import math
from datetime import datetime, timedelta

from sepal_ui import sepalwidgets as sw
from traitlets import Bool
from shapely_geojson import dumps

from component import widget as cw
from component.message import cm
from component import scripts as cs


class APIPlanetTile(sw.Card):
    """
    A card to select information from the Planet API
    """

    buffer = None
    "the buffer geometry as a geoseries"

    current_date = None
    "the date saved as a datetime object"

    def __init__(self, alert_model, map_):

        # listent to the alert model
        self.alert_model = alert_model

        # get the map as a member
        self.map = map_

        # add the base widgets
        self.close = sw.Icon(children=["mdi-close"], x_small=True)
        self.title = sw.CardTitle(
            class_="pa-0 ma-0", children=[sw.Spacer(), self.close]
        )

        # create the control widgets
        self.w_prev_month = cw.MapBtn(
            "fa fa-chevron-double-left", class_="ma-0", attributes={"increm": -20}
        )
        self.w_prev_day = cw.MapBtn(
            "fas fa-chevron-left", class_="ma-0", attributes={"increm": -1}
        )
        self.w_now = cw.MapBtn("fas fa-circle", class_="ma-0", attributes=None)
        self.w_next_day = cw.MapBtn(
            "fas fa-chevron-right", class_="ma-0", attributes={"increm": 1}
        )
        self.w_next_month = cw.MapBtn(
            "fas fa-chevron-double-right", class_="ma-0", attributes={"increm": 20}
        )
        self.w_date = sw.TextField(
            label=cm.view.planet.date.label,
            v_model=None,
            dense=True,
            class_="ml-1 mr-1",
            readonly=True,
        )

        # affreaget the btns
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
        row = sw.Row(
            align="center",
            class_="ma-1",
            children=[btn_list, self.w_date],
        )

        # create the planet control widgets
        super().__init__(
            class_="pa-1",
            children=[self.title, row],
            viz=False,
        )

        # add javascript event
        self.close.on_event("click", lambda *Args: self.hide())
        self.alert_model.observe(self._toggle_widget, "valid_key")
        self.alert_model.observe(self.load_data, "current_id")
        self.w_prev_month.on_event("click", self._month)
        self.w_prev_day.on_event("click", self._day)
        self.w_now.on_event("click", self._now)
        self.w_next_day.on_event("click", self._day)
        self.w_next_month.on_event("click", self._month)
        self.w_date.observe(self.update_image, "v_model")

    def update_image(self, change):

        print(self.w_date.v_model)

        # remove any existing image
        self.map.remove_layername(cm.map.layer.planet)

        # if nothing is selected exit immediately
        if self.w_date.v_model is None:
            return

        # build the start and end date ased on the planet parameters
        start = timedelta(days=-self.alert_model.days_before)
        end = timedelta(days=self.alert_model.days_after)

        print("bite")

        # retreive the layer from planet
        items = cs.get_planet_items(
            self.alert_model.api_key,
            self.buffer,
            self.current_day + start,
            self.current_day + end,
            self.alert_model.cloud_cover,
        )

        print("bite encore")
        print(items)

        # layer = TileLayer(
        #            url=param.PLANET_TILES_URL.format(
        #                row.item_type, row.id, self.model.api_key
        #            ),
        #            name=f"{row.item_type}, {row.date}",
        #            attribution="Imagery © Planet Labs Inc.",
        #        )
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
        feat = self.alert_model.gdf.loc[[change["new"]]].squeeze()

        # we buffer on a 10% bigger surface than the observed alert
        # minimal size is 200m
        size = math.sqrt(feat.surface / math.pi) * 0.1
        size = max(200, size)

        # create a buffer geometry
        self.buffer = feat.geometry.buffer(size, cap_style=3).__geo_interface__
        # self.buffer = feat.to_json()

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
