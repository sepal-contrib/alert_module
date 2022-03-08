from sepal_ui import sepalwidgets as sw

from component import widget as cw
from component import parameter as cp
from .setting_tile import SettingTile
from .metadata_tile import MetadataTile
from .ee_planet_tile import EEPlanetTile


class MapTile(sw.Tile):
    def __init__(self):

        # set the map in the center
        self.map = cw.AlertMap()

        # I decided to set the widgets here instead of in the map to avoid
        # complexity with model sharing
        self.settings = SettingTile(map_=self.map)
        self.metadata = MetadataTile(
            alert_model=self.settings.alert_view.alert_model,
            map_=self.map,
            aoi_model=self.settings.aoi_view.model,
        )
        self.ee_planet = EEPlanetTile(
            alert_model=self.settings.alert_view.alert_model, map_=self.map
        )

        # place them in the map
        self.map.add_widget_as_control(self.settings, "bottomright")
        self.map.add_widget_as_control(self.metadata, "bottomleft")
        self.map.add_widget_as_control(self.ee_planet, "topright", True)

        # link to the btn for activation
        self.map.parameters_btn.on_click(lambda *args: self.settings.toggle_viz())
        self.map.metadata_btn.on_click(lambda *args: self.metadata.toggle_viz())
        self.map.navigate_btn.on_click(lambda *args: self.ee_planet.toggle_viz())

        super().__init__(id_="map_tile", title="", inputs=[self.map])
