from ipyleaflet import WidgetControl
from IPython.display import Javascript, display
import ipyvuetify as v
from ipywidgets import Button, Layout

from component.message import cm


class FullScreenControl(WidgetControl):

    ICONS = ["expand", "compress"]
    METHODS = ["embed", "fullscreen"]

    def __init__(self, **kwargs):

        self.zoomed = False

        # create a btn
        self.w_btn = Button(
            tooltip=cm.map.control.fullscreen,
            icon=self.ICONS[self.zoomed],
            layout=Layout(
                width="30px", height="30px", line_height="30px", padding="0px"
            ),
        )

        # overwrite the widget set in the kwargs (if any)
        kwargs["widget"] = self.w_btn
        kwargs["position"] = kwargs.pop("position", "topleft")
        kwargs["transparent_bg"] = True

        # create the widget
        super().__init__(**kwargs)

        # add javascrip behaviour
        self.w_btn.on_click(self._on_click)

        # template with js behaviour
        self.template = v.VuetifyTemplate(
            template="""
        <script>
            {methods: {
                jupyter_fullscreen() {
                    var element = document.getElementsByClassName("leaflet-container")[0];
                    element.style.position = "fixed";
                    element.style.width = "100vw";
                    element.style.height = "100vh";
                    element.style.zIndex = 800;
                    element.style.top = 0;
                    element.style.left = 0;
                    window.dispatchEvent(new Event('resize'));
                },
                jupyter_embed() {
                    var element = document.getElementsByClassName("leaflet-container")[0];
                    element.style.position = "";
                    element.style.width = "";
                    element.style.height = "";
                    element.style.zIndex = "";
                    element.style.top = "";
                    element.style.left = "";
                    window.dispatchEvent(new Event('resize'));
                }
            }}
        </script>
        """
        )
        display(self.template)

    def _on_click(self, widget):

        # change the zoom state
        self.zoomed = not self.zoomed

        # change icon
        self.w_btn.icon = self.ICONS[self.zoomed]

        # zoom
        self.template.send({"method": self.METHODS[self.zoomed], "args": []})

        return
