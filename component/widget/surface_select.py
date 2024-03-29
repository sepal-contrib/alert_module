from ipywidgets import dlink
from sepal_ui import sepalwidgets as sw

from component.message import cm


class SurfaceSelect(sw.Col):
    def __init__(self):
        # define a title
        title = sw.Html(tag="h4", children=[cm.surface_select.label])

        # define the slider with the value vizualizer
        slider = sw.Slider(
            v_model=0, min=0, max=100, thumb_label=True, class_="mt-5", step=0.5
        )
        number = sw.TextField(suffix="ha", readonly=True, xs2=True)

        # create the widget
        super().__init__(children=[title, slider])

        # add links
        dlink((slider, "v_model"), (self, "v_model"))
        dlink((slider, "v_model"), (number, "v_model"))
