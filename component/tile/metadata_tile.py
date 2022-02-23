from sepal_ui import sepalwidgets as sw
from sepal_ui import color as sc

from component import widget as cw


class MetadataTile(sw.Card):
    """
    A card to display the metadata information relative to an alert
    """

    def __init__(self):

        # add the base widgets
        self.close = sw.Icon(children=["mdi-close"], small=True)
        self.title = sw.CardTitle(
            class_="pa-0 ma-0", children=[sw.Spacer(), self.close]
        )
        self.w_id = cw.DynamicSelect()
        self.w_alert = sw.TextField(
            small=True, readonly=True, children=[""], v_model=None
        )
        self.w_date = sw.TextField(
            small=True, readonly=True, children=[""], v_model=None
        )
        self.w_surface = sw.TextField(
            small=True, readonly=True, children=[""], v_model=None, suffix="ha"
        )
        self.w_review = sw.RadioGroup(
            small=True,
            row=True,
            v_model=None,
            children=[
                sw.Radio(label="yes", value=1, color=sc.success),
                sw.Radio(label="no", value=0, color=sc.error),
            ],
        )

        # add the default card buton and alert
        self.btn = sw.Btn("export", small=True)
        self.alert = sw.Alert(small=True)

        # create a table out of the widgets
        table = sw.SimpleTable(
            dense=True,
            children=[
                self.row("alert", self.w_alert),
                self.row("date", self.w_date),
                self.row("surface", self.w_surface),
                self.row("review", self.w_review),
            ],
        )

        # create the table
        super().__init__(
            class_="pa-1", children=[self.title, self.w_id, table, self.btn, self.alert]
        )

        # add javascript events
        self.close.on_event("click", lambda *args: self.hide())

    @staticmethod
    def row(header, widget):
        """wrapper function to create a row from a header and a widget"""

        th = sw.Html(tag="th", children=[header])
        td = sw.Html(tag="td", children=[widget])
        tr = sw.Html(tag="tr", children=[th, td])

        return tr
