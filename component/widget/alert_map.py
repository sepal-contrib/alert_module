from ipyleaflet import WidgetControl
from ipywidgets import Button, Layout
from sepal_ui import mapping as sm
import ipyvuetify as v


class AlertMap(sm.SepalMap):
    def __init__(self):
        default = "CartoDB.DarkMatter" if v.theme.dark is True else "CartoDB.Positron"

        super().__init__(["SATELLITE", default], zoom=4)

        # add a custom dc
        self.alert_dc = sm.DrawControl(
            self, rectangle={}, circle={}, polygon={}, position="topright"
        )

        # add the fullscreen button
        self.w_fullscreen = sm.FullScreenControl(
            self, position="topright", fullscreen=True, fullapp=True
        )

        self.add_control(self.w_fullscreen)
        self.add_control(self.alert_dc)
        self.layout.height = "90vh"

    def add_widget_as_control(self, widget, position, first=False):
        """
        Add widget as control in the given position

        Args:
            widget (dom.widget): Widget to convert as map control
            position (str): 'topleft', 'topright', 'bottomright', 'bottomlreft'
            first (Bool): Whether set the control as first or last element
        """

        new_control = WidgetControl(
            widget=widget, position=position, transparent_bg=True
        )

        if first == True:
            self.controls = tuple(
                [new_control] + [control for control in self.controls]
            )
        else:
            self.controls = self.controls + tuple([new_control])

        return
