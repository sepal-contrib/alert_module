import math
from datetime import datetime, timedelta

from sepal_ui import sepalwidgets as sw
from sepal_ui import color as sc
from sepal_ui.scripts import utils as su
import pandas as pd

from component import widget as cw
from component import parameter as cp


class MetadataTile(sw.Card):
    """
    A card to display the metadata information relative to an alert
    """

    def __init__(self, alert_model, map_, aoi_model):

        # listen the alert_model
        self.alert_model = alert_model
        self.aoi_model = aoi_model

        # get the map as a member
        self.map = map_

        # add the base widgets
        self.close = sw.Icon(children=["mdi-close"], small=True)
        self.title = sw.CardTitle(
            class_="pa-0 ma-0", children=[sw.Spacer(), self.close]
        )
        self.w_id = cw.DynamicSelect()
        self.w_alert = sw.TextField(small=True, readonly=True, v_model="")
        self.w_date = sw.TextField(small=True, readonly=True, v_model="")
        self.w_surface = sw.TextField(
            small=True, readonly=True, v_model="", suffix="ha"
        )
        self.w_coords = sw.TextField(small=True, readonly=True, v_model="")
        self.w_review = sw.RadioGroup(
            disabled=True,
            small=True,
            row=True,
            v_model="unset",
            children=[
                sw.Radio(label="yes", value="yes", color=sc.success),
                sw.Radio(label="no", value="no", color=sc.error),
                sw.Radio(label="unset", value="unset", color=sc.info),
            ],
        )

        # add the default card buton and alert
        self.btn = sw.Btn("export", small=True)
        btn_list = sw.Row(children=[sw.Spacer(), self.btn, sw.Spacer()])
        self.alert = sw.Alert(small=True)

        # create a table out of the widgets
        table = sw.SimpleTable(
            dense=True,
            children=[
                self.row("alert", self.w_alert),
                self.row("date", self.w_date),
                self.row("surface", self.w_surface),
                self.row("coords", self.w_coords),
                self.row("review", self.w_review),
            ],
        )

        # create the metadata object
        super().__init__(
            class_="pa-1",
            children=[self.title, self.w_id, table, btn_list, self.alert],
            viz=False,
        )

        # add javascript events
        self.close.on_event("click", lambda *args: self.hide())
        self.alert_model.observe(self._on_alerts_change, "gdf")
        self.w_id.observe(self._on_id_change, "v_model")
        self.w_review.observe(self._on_review_change, "v_model")
        self.btn.on_event("click", self.export)
        self.alert_model.observe(self._id_click, "current_id")

    def _id_click(self, change):
        """
        reflect the current id change in the metadata
        this change is triggered when an feature is clicked on the map
        """

        if change["new"] is not None:
            self.w_id.v_model = change["new"]

        return

    def _on_review_change(self, change):
        """adapt the value of review in the model dataframe"""

        # exit if id is not set
        # replacing the alerts will trigger it
        if self.w_id.v_model is None:
            return

        # set the value in the dataframe
        self.alert_model.gdf.at[self.w_id.v_model - 1, "review"] = change["new"]

        return

    def _on_id_change(self, change):
        """
        set the table values according to the selected id data
        zoom on the alert geometry
        """

        if change["new"] is None:
            self.w_alert.v_model = ""
            self.w_date.v_model = ""
            self.w_surface.v_model = ""
            self.w_coords.v_model = ""
            self.w_review.v_model = "unset"
            self.w_review.disabled = True
        else:

            # select the geoseries
            feat = self.alert_model.gdf.loc[
                self.alert_model.gdf.id == change["new"]
            ].squeeze()

            # set the alert type
            alert_types = ["undefined", "confirmed", "potential"]
            self.w_alert.v_model = alert_types[feat.alert]

            # read back the date in a readable format
            julian, year = math.modf(feat.date)
            julian = int(julian * 100)
            date = datetime(int(year), 1, 1) + timedelta(days=julian - 1)
            self.w_date.v_model = date.strftime("%Y-%m-%d")

            # read the surface
            self.w_surface.v_model = feat.surface

            # get the center coordinates
            coords = list(feat.geometry.centroid.coords)[0]
            self.w_coords.v_model = f"({coords[0]:.5f}, {coords[1]:.5f})"

            # get the review value
            self.w_review.v_model = feat.review
            self.w_review.disabled = False

            # zoom the map on the geometry
            self.map.zoom_bounds(feat.geometry.bounds)

            # change the id in the model
            self.alert_model.current_id = change["new"]

            return

    def _on_alerts_change(self, change):

        self.w_id.v_model = None

        if self.alert_model.gdf is None:
            return

        # update the dynamic select
        id_list = self.alert_model.gdf.id.tolist()
        self.w_id.set_items(id_list)

        # show the table
        self.show()

        return self

    @su.loading_button(debug=True)
    def export(self, widget, event, data):
        """export the datapoint to a specific file location"""

        # copy the gdf locally
        gdf = self.alert_model.gdf.copy()

        # add the lat and long column
        gdf["lat"] = gdf.apply(lambda r: list(r.geometry.centroid.coords)[0][0], axis=1)
        gdf["lng"] = gdf.apply(lambda r: list(r.geometry.centroid.coords)[0][1], axis=1)

        # remove the geometries
        df = pd.DataFrame(gdf.drop(columns="geometry"))

        # create the name of the output from the paramters
        name = f"{self.aoi_model.name}_{self.alert_model.start}_{self.alert_model.end}_{self.alert_model.min_size}"
        path = cp.result_dir / f"{name}.csv"

        # export the file
        df.to_csv(path, index=False)

        return

    @staticmethod
    def row(header, widget):
        """wrapper function to create a row from a header and a widget"""

        th = sw.Html(tag="th", children=[header])
        td = sw.Html(tag="td", children=[widget])
        tr = sw.Html(tag="tr", children=[th, td])

        return tr
