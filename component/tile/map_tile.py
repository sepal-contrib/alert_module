from sepal_ui import sepalwidgets as sw
from sepal_ui import mapping as sm
from ipyleaflet import WidgetControl

from component import widget as cw
from component import parameter as cp

from .ee_planet_tile import EEPlanetTile
from .api_planet_tile import APIPlanetTile
from .aoi_control import *
from .alert_control import *
from .planet_control import *
from .metadata_control import *


class MapTile(sw.Tile):
    def __init__(self):

        # set the map in the center
        self.map = cw.AlertMap()

        # I decided to set the widgets here instead of in the map to avoid
        # complexity with model sharing
        self.aoi_control = AoiControl(self.map)
        self.alert_control = AlertControl(self.aoi_control.view.model, self.map)
        self.planet_control = PlanetControl(
            self.alert_control.view.alert_model, self.map
        )

        # add the control on the map
        self.map.add_control(self.planet_control)
        self.map.add_control(self.alert_control)
        self.map.add_control(self.aoi_control)

        # extract the model from the setting tile for easier manipulation
        self.aoi_model = self.aoi_control.view.model
        self.alert_model = self.alert_control.view.alert_model

        # create the other tiles
        self.metadata_control = MetadataControl(
            self.alert_model, self.map, self.aoi_model
        )
        self.metadata = self.metadata_control.view
        self.ee_planet = EEPlanetTile(self.alert_model, self.map)
        self.api_planet = APIPlanetTile(
            self.alert_model, self.map, self.planet_control.view.model
        )

        # place them in the map
        self.map.add_control(self.metadata_control)
        self.map.add_widget_as_control(self.ee_planet, "topright", True)
        self.map.add_widget_as_control(self.api_planet, "topright", True)

        # link to the btn for activation
        self.aoi_control.view.observe(self.end_aoi, "updated")
        self.alert_control.view.observe(self.end_alert, "updated")
        self.planet_control.view.observe(self.end_planet, "updated")

        super().__init__(id_="map_tile", title="", inputs=[self.map])

    def end_aoi(self, change):
        """switch to alert selection when the aoi is selected"""

        self.alert_control.menu.v_model = True

        return

    def end_alert(self, change):
        """close the alert selection once done, Planet need to be seen as an option"""

        self.alert_control.menu.v_model = False

        return

    def end_planet(self, change):
        """close the planet selection once done"""

        if self.planet_control.view.alert.type == "success":
            self.planet_control.menu.v_model = False

        return

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

    def set_code(self, link):
        "add the code link btn to the map"

        btn = sm.MapBtn("fa-solid fa-code", href=link, target="_blank")
        control = WidgetControl(widget=btn, position="bottomleft")
        self.map.add_control(control)

        return

    def set_wiki(self, link):
        "add the wiki link btn to the map"

        btn = sm.MapBtn("fa-solid fa-book-open", href=link, target="_blank")
        control = WidgetControl(widget=btn, position="bottomleft")
        self.map.add_control(control)

        return

    def set_issue(self, link):
        "add the code link btn to the map"

        btn = sm.MapBtn("fa-solid fa-bug", href=link, target="_blank")
        control = WidgetControl(widget=btn, position="bottomleft")
        self.map.add_control(control)

        return
