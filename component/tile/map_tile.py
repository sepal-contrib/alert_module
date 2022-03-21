from sepal_ui import sepalwidgets as sw

from component import widget as cw
from component import parameter as cp
from .setting_tile import SettingTile
from .metadata_tile import MetadataTile
from .ee_planet_tile import EEPlanetTile
from .api_planet_tile import APIPlanetTile


class MapTile(sw.Tile):
    def __init__(self):

        # set the map in the center
        self.map = cw.AlertMap()

        # I decided to set the widgets here instead of in the map to avoid
        # complexity with model sharing
        self.settings = SettingTile(self.map)

        # extract the model from the setting tile for easier manipulation
        self.aoi_model = self.settings.aoi_view.model
        self.alert_model = self.settings.alert_view.alert_model

        # create the other tiles
        self.metadata = MetadataTile(self.alert_model, self.map, self.aoi_model)
        self.ee_planet = EEPlanetTile(self.alert_model, self.map)
        self.api_planet = APIPlanetTile(self.alert_model, self.map)

        # place them in the map
        self.map.add_widget_as_control(self.settings, "bottomright")
        self.map.add_widget_as_control(self.metadata, "bottomleft")
        self.map.add_widget_as_control(self.ee_planet, "topright", True)
        self.map.add_widget_as_control(self.api_planet, "topright", True)

        # link to the btn for activation
        self.map.parameters_btn.on_click(lambda *args: self.settings.toggle_viz())
        self.map.metadata_btn.on_click(lambda *args: self.metadata.toggle_viz())
        self.map.navigate_btn.on_click(self._toggle_planet_viz)

        super().__init__(id_="map_tile", title="", inputs=[self.map])

    def _toggle_planet_viz(self, *args):
        """
        Don't toogle the same planet widget based on the API key
        If the planet API key is validated we'll use NICFI Level 2 data and the Planet API
        if not we fallback to pure GEE and NICFI level 1
        """

        model = self.alert_model

        if model.valid_key is False:
            self.ee_planet.toggle_viz()
        elif model.valid_key is True:
            self.api_planet.toggle_viz()

        return
