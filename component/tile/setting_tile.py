from sepal_ui import sepalwidgets as sw
from ipywidgets import link

from component import widget as cw
from component.message import cm
from .alert_view import AlertView
from .aoi_view import AoiView
from .planet_view import PlanetView


class SettingTile(sw.Card):
    def __init__(self, map_):

        # save the map as a member
        # for the zoom change option
        self.map = map_

        # create the 2 subtiles
        self.aoi_view = AoiView(map_=map_)
        self.alert_view = AlertView(self.aoi_view.model, map_)
        self.planet_view = PlanetView(self.alert_view.alert_model)

        # set them into a tab widget
        self.tabs = sw.Tabs(
            fixed_tabs=True,
            v_model=0,
            children=[
                sw.Tab(children=[cm.view.setting.aoi], key=0),
                sw.Tab(children=[cm.view.setting.planet], key=1),
                sw.Tab(children=[cm.view.setting.alert], key=2),
            ],
        )

        contents = sw.TabsItems(
            class_="mt-5",
            v_model=0,
            children=[
                sw.TabItem(children=[self.aoi_view], key=0),
                sw.TabItem(children=[self.planet_view], key=1),
                sw.TabItem(children=[self.alert_view], key=2),
            ],
        )

        # add parameter to close the widget
        self.close = sw.Icon(children=["mdi-close"], small=True)
        title = sw.CardTitle(class_="pa-0 ma-0", children=[sw.Spacer(), self.close])

        # create the card
        super().__init__(
            children=[title, self.tabs, contents],
            max_height="80vh",  # prevent from going outside the map
            min_width="30vw",
            max_width="30vw",
            class_="pa-2",
        )

        # add js behaviour
        self.close.on_event("click", lambda *args: self.toggle_viz())
        link((self.tabs, "v_model"), (contents, "v_model"))
        self.alert_view.alert_model.observe(self._hide_on_success, "gdf")
        self.tabs.observe(self.update_zoom, "v_model")

    def _hide_on_success(self, change):
        """hide the tile if alerts are loaded on the map"""

        if change["new"] is not None:
            self.hide()

        return self

    def update_zoom(self, change):
        """
        Update the zoom based on the selected panel
        - If no AOI is selected, we do nothing
        - AOI and planet we zoom on the aoi
        - alert we zoom on the world to see the alert footprint
        """

        # do nothing if no AOI
        if self.aoi_view.model.gdf is None:
            return

        # aoi selection and planet
        if self.tabs.v_model == 0 or self.tabs.v_model == 1:
            self.map.zoom_ee_object(self.aoi_view.model.feature_collection.geometry())
        # alert selection
        elif self.tabs.v_model == 2:
            self.map.zoom = 2
            self.map.center = [0, 0]

        return
