import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from sepal_ui import color as sc


class MapBtn(v.Btn, sw.SepalWidget):
    """
    Wrapper of Btn objects to embed some default formating options that will be used
    in many different widgets of the map. THis button is by design:
    without text, blue, x_small and with 1 single icon
    it remains fully customizable but for the chidlren trait
    """

    def __init__(self, icon_name, **kwargs):

        # set the default parameters
        kwargs["color"] = kwargs.pop("color", sc.secondary)
        kwargs["x_small"] = kwargs.pop("x_small", True)
        kwargs["class_"] = kwargs.pop("class_", "ml-1 mr-1")
        kwargs["children"] = [sw.Icon(children=[icon_name])]  # , x_small=True)]
        kwargs["style"] = "padding-top: 2px; padding-bottom: 2px;"

        super().__init__(**kwargs)
