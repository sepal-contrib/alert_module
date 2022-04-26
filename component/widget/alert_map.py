from ipyleaflet import WidgetControl
from ipywidgets import Button, Layout
from sepal_ui import mapping as sm
from .fullscreen_control import FullScreenControl

from component.message import cm


class CButton(Button):
    def __init__(self, tooltip, icon):
        super().__init__(
            tooltip=tooltip,
            icon=icon,
            layout=Layout(
                width="30px", height="30px", line_height="30px", padding="0px"
            ),
        )


class AlertMap(sm.SepalMap):
    def __init__(self):

        super().__init__(dc=True, zoom=3)

        self.hide_dc()
        self.layout.height = "85vh"

        # add the fullscreen button
        self.add_control(FullScreenControl())

        # add the buttons on the topleft side of the map
        self.parameters_btn = CButton(cm.map.control.parameter, "navicon")
        self.navigate_btn = CButton(cm.map.control.navigate, "globe")
        self.metadata_btn = CButton(cm.map.control.metadata, "info")

        self.add_widget_as_control(self.parameters_btn, "topleft")
        self.add_widget_as_control(self.navigate_btn, "topleft")
        self.add_widget_as_control(self.metadata_btn, "topleft")

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

    def remove_layername(self, name):
        """remove a layer if existing by its name"""

        try:
            layer = next(l for l in self.layers if l.name == name)
            self.remove_layer(layer)
        except StopIteration:
            pass

        return
