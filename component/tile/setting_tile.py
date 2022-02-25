from sepal_ui import sepalwidgets as sw
from ipywidgets import link

from component import widget as cw
from .alert_view import AlertView


class SettingTile(sw.Card):
    def __init__(self, map_):

        # create the 2 subtiles
        self.aoi_view = cw.CustomAoiView(map_=map_)
        self.alert_view = AlertView(self.aoi_view.model, map_)

        # set them into a tab widget
        tabs = sw.Tabs(
            fixed_tabs=True,
            v_model=0,
            children=[
                sw.Tab(children=["AOI"], key=0),
                sw.Tab(children=["Alerts"], key=1),
            ],
        )

        contents = sw.TabsItems(
            class_="mt-5",
            v_model=0,
            children=[
                sw.TabItem(children=[self.aoi_view], key=0),
                sw.TabItem(children=[self.alert_view], key=1),
            ],
        )

        # add parameter to close the widget
        self.close = sw.Icon(children=["mdi-close"], small=True)
        title = sw.CardTitle(class_="pa-0 ma-0", children=[sw.Spacer(), self.close])

        # create the card
        super().__init__(
            children=[title, tabs, contents],
            min_height="370px",
            min_width="462px",
            max_width="462px",
            class_="pa-2",
        )

        # add js behaviour
        self.close.on_event("click", lambda *args: self.toggle_viz())
        link((tabs, "v_model"), (contents, "v_model"))
        self.alert_view.alert_model.observe(self._hide_on_success, "gdf")

    def _hide_on_success(self, change):
        """hide the tile if alerts are loaded on the map"""

        if change["new"] is not None:
            self.hide()

        return self
