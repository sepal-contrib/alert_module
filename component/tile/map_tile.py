from sepal_ui import sepalwidgets as sw

from component import widget as cw


class MapTile(sw.Tile):
    def __init__(self):

        # set the map in the center
        self.map = cw.AlertMap()

        # I decided to set the widgets here instead of in the map to avoid
        # complexity with model sharing
        self.select = cw.DynamicSelect()

        # place them in the map
        self.map.add_widget_as_control(self.select, "topright", True)

        # link to the btn for activation
        self.map.navigate_btn.on_click(lambda *args: self.select.toggle_viz())

        super().__init__(id_="map_tile", title="Map tile", inputs=[self.map])
