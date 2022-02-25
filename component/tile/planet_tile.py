import math
from datetime import datetime, timedelta

from sepal_ui import sepalwidgets as sw
from sepal_ui import color as sc
import ipyvuetify as v
from traitlets import Bool, Any
import ee
from ipyleaflet import GeoJSON

from component import widget as cw
from component import parameter as cp
from component import scripts as cs


class PlanetTile(sw.Card):
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

        # add the base widgets
        self.close = sw.Icon(children=["mdi-close"], x_small=True)
        self.title = sw.CardTitle(
            class_="pa-0 ma-0", children=[sw.Spacer(), self.close]
        )

        # create the control widgets
        self.w_color = cw.MapBtn("fas fa-palette")
        self.w_prev = cw.MapBtn("fas fa-chevron-left", class_="ma-0")
        self.w_now = cw.MapBtn("far fa-circle", class_="ma-0")
        self.w_next = cw.MapBtn("fas fa-chevron-right", class_="ma-0")
        self.w_date = sw.Select(
            label="dates", items=[], v_model=None, dense=True, class_="ml-1 mr-1"
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
            class_="pa-1",
            children=[self.title, row],
            viz=False,
        )

        # add javascript events
        self.close.on_event("click", lambda *args: self.hide())
        self.alert_model.observe(self.load_dates, "current_id")
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
        self.remove_planet_layer()

        # exit if nothing is selected
        if self.w_date.v_model is None:
            return

        # check if the btn need to be hidden
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
        self.map.addLayer(planet_image, viz_params, "planet")

        return

    def load_dates(self, change):
        """
        load the available image date for the custom feature
        """

        # unable the widget
        self.unable()

        # reset date values
        # to triger a reload if we change point without changing date
        self.w_date.items = []
        self.w_date.v_model = None

        # extract the geometry
        feat = self.alert_model.gdf.loc[[change["new"] - 1]].squeeze()

        # we buffer on a 10% bigger surface than the observed alert
        # minimal size is 1 km
        size = math.sqrt(feat.surface * 10000 / math.pi) * 0.1
        size = max(200, size)

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
        self.w_date.items = date_items

        # show the widget
        self.show()

        # go to the now item
        self.now_(None, None, None)

        return

    def remove_planet_layer(self):
        """
        remove the planet layer if existing to avoid duplication
        """

        try:
            layer = next(l for l in self.map.layers if l.name == "planet")
            self.map.remove_layer(layer)
        except StopIteration:
            pass

        return

    def prev_(self, widget, event, data):
        """got to previous items in the list"""

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

    def next_(self, widget, event, data):
        """got to next items in the list"""

        if self.w_date.v_model is None:
            index = len(self.w_date.items)
        else:
            index = next(
                i
                for i, v in enumerate(self.w_date.items)
                if v["value"] == self.w_date.v_model
            )
            index = min(len(self.w_date.items), index + 1)

        # change the dates widget value
        self.w_date.v_model = self.w_date.items[index]["value"]

        return

    def now_(self, widget, event, data):
        """search for the current_date in the list and change the w_date value to the appropiate interval"""

        # extract the current date as an integer timestamp
        julian, year = math.modf(
            self.alert_model.gdf.at[(self.alert_model.current_id - 1), "date"]
        )
        julian = int(julian * 100)
        date = (
            datetime(int(year), 1, 1) + timedelta(days=julian - 1)
        ).timestamp() * 1000

        # find it's closest index in the dates list
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
            self.w_prev.disabled = True
        elif index == len(self.w_date.items):
            self.w_next.disabled = True

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
