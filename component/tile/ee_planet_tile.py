import math
from datetime import datetime, timedelta

from sepal_ui import sepalwidgets as sw
from sepal_ui import color as sc
from sepal_ui.scripts import utils as su
import ipyvuetify as v
from traitlets import Bool, Any
import ee
from ipyleaflet import GeoJSON

from component import widget as cw
from component import parameter as cp
from component import scripts as cs
from component.message import cm


class EEPlanetTile(sw.Card):
    """
    A card to select the information from the planet imagery
    """

    BANDS = [["R", "G", "B"], ["N", "R", "G"]]
    "the available bands displays"

    color = Bool(False).tag(sync=True)
    "the bool value to select the coloring 0: RGB, 1: NRG"

    current_date = None
    "the date saved as a string"

    buffer = None
    "the buffer geometry as an ee.FeatureCollection"

    nicfi = None
    "the ImageCollection of the nicfi images"

    def __init__(self, alert_model, map_):

        # listen the alert_model
        self.alert_model = alert_model

        # get the map as a member
        self.map = map_

        # create the control widgets
        self.w_color = cw.MapBtn("fa-solid fa-palette")
        self.w_prev = cw.MapBtn("mdi-chevron-left", class_="ma-0")
        self.w_now = cw.MapBtn("far fa-circle", class_="ma-0")
        self.w_next = cw.MapBtn("mdi-chevron-right", class_="ma-0")
        self.w_date = sw.Select(
            label=cm.ee_planet.date.label,
            items=[],
            v_model=None,
            dense=True,
            class_="ml-1 mr-1",
            clearable=True,
        )

        # agregate the btns
        btn_list = sw.ItemGroup(
            class_="mr-1 ml-1 v-btn-toggle",
            children=[self.w_prev, self.w_now, self.w_next],
        )

        # create a line with all the widgets
        row = sw.Row(
            align="center",
            class_="ma-1",
            children=[self.w_color, btn_list, self.w_date],
        )

        # disable before any point is selected
        self.disable()

        # create the planet control widgets
        super().__init__(
            class_="pa-2",
            children=[row],
            viz=False,
            max_height="80vh",
            max_width="80vw",
        )

        # add javascript events
        self.alert_model.observe(self.load_dates, "current_id")
        self.alert_model.observe(self._toggle_widget, "valid_key")
        self.w_prev.on_event("click", self.prev_)
        self.w_next.on_event("click", self.next_)
        self.w_now.on_event("click", self.now_)
        self.w_date.observe(self.update_layer, "v_model")
        self.observe(self.update_layer, "color")
        self.w_color.on_event("click", self._on_palette_change)

    def _on_palette_change(self, widget, event, data):
        """switch the value of the palette choice"""

        self.color = not self.color

        return

    def update_layer(self, change):
        """
        update the layer according to the new parameters
        can be triggered by the color change or the date change
        """

        # remove the previous layer
        self.map.remove_layer(cm.ee_planet.layer.name, none_ok=True)
        self.free_btn(None)

        # exit if nothing is selected
        # and enable all the btns
        if self.w_date.v_model is None:
            return

        # check if the btn needs to be hidden
        index = next(
            i
            for i, v in enumerate(self.w_date.items)
            if v["value"] == self.w_date.v_model
        )
        self.free_btn(index)

        # retreive the layer from GEE
        start = self.w_date.v_model[0]
        planet_image = self.nicfi.filter(
            ee.Filter.eq("system:time_start", start)
        ).first()

        # cut it to the buffer boundaries
        planet_image = planet_image.clipToBoundsAndScale(
            geometry=self.buffer, scale=4.77
        )

        # get the color
        viz_params = {**cp.planet_viz, "bands": self.BANDS[self.color]}

        # display the layer on the map
        self.map.addLayer(planet_image, viz_params, cm.ee_planet.layer.name)

        return

    def load_dates(self, change):
        """
        load the available image date for the custom feature
        """

        # exit straigh away if an API key is validated
        if self.alert_model.valid_key is True:
            return

        # unable the widget
        self.unable()

        # reset date values
        # to triger a reload if we change point without changing date
        self.w_date.items = []
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
        size = max(1000, size)

        # create a buffer geometry
        self.buffer = ee.Geometry(feat.geometry.__geo_interface__).buffer(size).bounds()

        # create the planet Image collection member
        self.nicfi = (
            ee.ImageCollection(cp.planet_africa)
            .filterBounds(self.buffer)
            .merge(ee.ImageCollection(cp.planet_america).filterBounds(self.buffer))
            .merge(ee.ImageCollection(cp.planet_asia).filterBounds(self.buffer))
        )

        # load the dates
        start_list = self.nicfi.aggregate_array("system:time_start").getInfo()
        end_list = self.nicfi.aggregate_array("system:time_end").getInfo()
        name_list = self.nicfi.aggregate_array("system:index").getInfo()

        date_items = []
        for i in range(len(start_list)):  # I consider all the list the same size
            text = cs.planet_moasics(name_list[i])
            value = [start_list[i], end_list[i]]
            item = {"text": text, "value": value}
            date_items += [item]

        # reverse the list so that the most recent come on top
        self.w_date.items = date_items[::-1]

        # show the widget
        self.show()

        # go to the now item
        self.now_(None, None, None)

        return

    def next_(self, widget, event, data):
        """got to next items in time (in the future)"""

        if self.w_date.v_model is None:
            index = 0
        else:
            index = next(
                i
                for i, v in enumerate(self.w_date.items)
                if v["value"] == self.w_date.v_model
            )
            index = max(0, index - 1)

        # change the dates widget value
        self.w_date.v_model = self.w_date.items[index]["value"]

        return

    def prev_(self, widget, event, data):
        """got to prev items in time (in the past)"""

        if self.w_date.v_model is None:
            index = len(self.w_date.items) - 1
        else:
            index = next(
                i
                for i, v in enumerate(self.w_date.items)
                if v["value"] == self.w_date.v_model
            )
            index = min(len(self.w_date.items) - 1, index + 1)

        # change the dates widget value
        self.w_date.v_model = self.w_date.items[index]["value"]

        return

    def now_(self, widget, event, data):
        """search for the current_date in the list and change the w_date value to the appropiate interval"""

        # extract the current date as an integer timestamp
        julian, year = math.modf(
            self.alert_model.gdf.at[(self.alert_model.current_id), "date"]
        )
        julian = int(julian * 1000)
        date = (
            datetime(int(year), 1, 1) + timedelta(days=julian - 1)
        ).timestamp() * 1000

        # find it's closest index in the dates list
        # remember that the list is in reversed chronological order
        index = next(
            i
            for i, v in enumerate(self.w_date.items)
            if v["value"][0] <= date <= v["value"][1]
        )

        # change the dates widget value
        self.w_date.v_model = self.w_date.items[index]["value"]

        return

    def free_btn(self, index):
        """free all the selectors according to the selected index"""

        self.w_prev.disabled = False
        self.w_next.disabled = False

        if index == 0:
            self.w_next.disabled = True
        elif index == len(self.w_date.items) - 1:
            self.w_prev.disabled = True

        return

    def unable(self):
        """unable the whole widget"""

        self.w_color.disabled = False
        self.w_prev.disabled = False
        self.w_now.disabled = False
        self.w_next.disabled = False
        self.w_date.disabled = False

        return self

    def disable(self):
        """disable the whole widget"""

        self.w_color.disabled = True
        self.w_prev.disabled = True
        self.w_now.disabled = True
        self.w_next.disabled = True
        self.w_date.disabled = True

        return self

    def _toggle_widget(self, change):
        """
        change visibility and displayed information based on the API status
        Only used to close the widget if the value were displayed before the
        validation of the API key
        """

        if change["new"] is True:
            self.w_date.v_model = None
            self.disable()
            self.hide()

        return
