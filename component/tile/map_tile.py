from sepal_ui import sepalwidgets as sw
from sepal_ui import aoi

from component import widget as cw


class MapTile(sw.Tile):
    def __init__(self):

        # set the map in the center
        self.map = cw.AlertMap()

        # I decided to set the widgets here instead of in the map to avoid
        # complexity with model sharing
        self.select = cw.DynamicSelect()
        self.aoi_selector = aoi.AoiView(methods=["-DRAW", "-POINTS"], map_=self.map)

        # place them in the map
        self.map.add_widget_as_control(self.select, "topright", True)
        self.map.add_widget_as_control(self.aoi_selector, "bottomright")

        # link to the btn for activation
        self.map.navigate_btn.on_click(lambda *args: self.select.toggle_viz())
        self.map.parameters_btn.on_click(lambda *args: self.aoi_selector.toggle_viz())

        super().__init__(id_="map_tile", title="Map tile", inputs=[self.map])
