import math

from sepal_ui import sepalwidgets as sw
from sepal_ui import color as sc
import ipyvuetify as v
from traitlets import Bool, Any
import ee

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

        # create the planet control widgets
        super().__init__(
            class_="pa-1",
            children=[self.title, row],
            viz=True,
        )

        # add javascript events
        self.close.on_event("click", lambda *args: self.hide())
        self.alert_model.observe(self.load_dates, "id_loaded")

    def _on_palette_change(self, widget, event, data):
        """switch the value of the palette choice"""

        self.color = not self.color

        return

    def update_layer(self, change):
        """
        update the layer according to the new parameters
        can be triggered by the color change or the date change
        """

        pass

    def load_dates(self, change):
        """
        load the available image date for the custom feature
        """

        # remove the exisiting planet layer
        self.remove_planet_layer()

        # extract the geometry
        feat = self.alert_model.gdf.loc[[change["new"] - 1]].squeeze()

        # we buffer on a 10% bigger surface than the observed alert
        size = math.sqrt(feat.surface * 10000 / math.pi) * 0.1

        # create a buffer geometry
        self.buffer = ee.Geometry(feat.geometry.__geo_interface__).buffer(size).bounds()

        # display it on the map
        self.map.addLayer(self.buffer, {"color": "green"}, "buffer")

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

        return

    def prev_next(self, change):
        """
        select the next image according to the widget value
        """

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
