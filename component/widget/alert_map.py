from ipyleaflet import FullScreenControl, WidgetControl
from ipywidgets import Button, Layout
from sepal_ui import mapping as sm


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

        super().__init__(dc=True)

        self.hide_dc()

        # add the fullscreen button
        self.add_control(FullScreenControl(position="topright"))

        # add the buttons on the topleft side of the map
        self.parameters_btn = CButton("Toggle parameters", "navicon")
        self.navigate_btn = CButton("Navigate through Alerts", "globe")
        self.metadata_btn = CButton("Fire alert metadata", "info")

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
