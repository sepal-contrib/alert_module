from sepal_ui import sepalwidgets as sw

from component import widget as cw


class MapTile(sw.Tile):
    def __init__(self):

        # set the map in the center
        self.map = cw.AlertMap()

        super().__init__(id_="map_tile", title="Map tile", inputs=[self.map])
