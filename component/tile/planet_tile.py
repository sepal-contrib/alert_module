from sepal_ui import sepalwidgets as sw
from sepal_ui import color as sc
import ipyvuetify as v


class PlanetTile(sw.Card):
    """
    A card to select the information from the planet imagery
    """

    def __init__(self, alert_model, map_):

        # listen the alert_model
        self.alert_model = alert_model

        # get the map as a member
        self.map = map_

        # add the base widgets
        self.close = sw.Icon(children=["mdi-close"], x_small=True)
        self.title = sw.CardTitle(
            class_="pa-0 ma-0", children=[sw.Spacer(), self.close]
        )

        # create the control widgets
        self.w_color = v.Btn(
            children=[sw.Icon(children=["mdi-palette"], small=True)],
            color=sc.secondary,
            x_small=True,
            class_="ma-1",
        )
        self.w_date = sw.Select(
            label="dates", items=[], v_model=None, dense=True, class_="ma-1"
        )
        self.w_prev = v.Btn(
            children=[sw.Icon(children=["mdi-chevron-left"], small=True)],
            color=sc.secondary,
            x_small=True,
        )
        self.w_now = v.Btn(
            children=[sw.Icon(children=["mdi-circle-outline"], x_small=True)],
            color=sc.secondary,
            x_small=True,
        )
        self.w_next = v.Btn(
            children=[sw.Icon(children=["mdi-chevron-right"], small=True)],
            color=sc.secondary,
            x_small=True,
        )

        # agregate the btns
        btn_list = sw.BtnToggle(
            class_="ma-1", children=[self.w_prev, self.w_now, self.w_next]
        )

        # create a line with all the widgets
        row = sw.Row(
            align="center",
            class_="ma-1",
            children=[self.w_color, btn_list, self.w_date],
        )

        # create the planet control widgets
        super().__init__(
            class_="pa-1",
            children=[self.title, row],
            viz=True,
        )

        # add javascript events
        self.close.on_event("click", lambda *args: self.hide())
