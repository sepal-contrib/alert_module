from sepal_ui import sepalwidgets as sw
from ipywidgets import link

from component import widget as cw


class SettingTile(sw.Card):
    def __init__(self, map_):

        # create the 2 subtiles
        self.aoi_view = cw.CustomAoiView(map_=map_)

        # set them into a tab widget
        tabs = sw.Tabs(v_model=0, children=[sw.Tab(children=["AOI"], key=0)])

        contents = sw.TabsItems(
            class_="mt-5",
            v_model=0,
            children=[sw.TabItem(children=[self.aoi_view], key=0)],
        )

        # add parameter to close the widget
        self.close = sw.Icon(children=["mdi-close"])
        title = sw.CardTitle(children=["Settings", sw.Spacer(), self.close])

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
