import math
from datetime import datetime, timedelta

from sepal_ui import sepalwidgets as sw
from sepal_ui import color as sc
from sepal_ui.scripts import utils as su
from sepal_ui import mapping as sm
import pandas as pd
from ipyleaflet import GeoJSON
import geopandas as gpd
import fiona

from component import widget as cw
from component import parameter as cp
from component.message import cm


class MetadataView(sw.Card):
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
        self.w_id = cw.DynamicSelect()
        self.w_alert = sw.TextField(small=True, readonly=True, v_model="")
        self.w_date = sw.TextField(small=True, readonly=True, v_model="")
        self.w_surface = sw.TextField(
            small=True, readonly=True, v_model="", suffix="px"
        )
        self.w_coords = sw.TextField(small=True, readonly=True, v_model="")
        self.w_review = sw.RadioGroup(
            disabled=True,
            small=True,
            row=True,
            v_model="unset",
            children=[
                sw.Radio(
                    label=cm.view.metadata.status.valid, value="yes", color=sc.success
                ),
                sw.Radio(
                    label=cm.view.metadata.status.unvalid, value="no", color=sc.error
                ),
                sw.Radio(
                    label=cm.view.metadata.status.unset, value="unset", color=sc.info
                ),
            ],
        )

        # add the default card buton and alert
        self.btn_csv = sw.Btn(
            cm.view.metadata.btn.csv,
            small=True,
            disabled=True,
            attributes={"data": "csv"},
        )
        self.btn_gpkg = sw.Btn(
            cm.view.metadata.btn.gpkg,
            small=True,
            disabled=True,
            attributes={"data": "gpkg"},
        )
        self.btn_kml = sw.Btn(
            cm.view.metadata.btn.kml,
            small=True,
            disabled=True,
            attributes={"data": "kml"},
        )
        btn_list = sw.Row(
            children=[
                sw.Spacer(),
                self.btn_csv,
                sw.Spacer(),
                self.btn_gpkg,
                sw.Spacer(),
                self.btn_kml,
                sw.Spacer(),
            ]
        )
        self.alert = sw.Alert(small=True)

        # create a table out of the widgets
        table = sw.SimpleTable(
            dense=True,
            children=[
                self.row(cm.view.metadata.row.alert, self.w_alert),
                self.row(cm.view.metadata.row.date, self.w_date),
                self.row(cm.view.metadata.row.pixels, self.w_surface),
                self.row(cm.view.metadata.row.coords, self.w_coords),
                self.row(cm.view.metadata.row.review, self.w_review),
            ],
        )

        # create the metadata object
        super().__init__(
            class_="pa-1",
            children=[self.w_id, table, btn_list, self.alert],
            max_height="50vh",
            max_width="20vw",
            min_width="20vw",
        )

        # add javascript events
        self.alert_model.observe(self._on_alerts_change, "gdf")
        self.w_id.observe(self._on_id_change, "v_model")
        self.w_review.observe(self._on_review_change, "v_model")
        self.btn_csv.on_event("click", self.export)
        self.btn_gpkg.on_event("click", self.export)
        self.btn_kml.on_event("click", self.export)
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
        self.alert_model.gdf.at[self.w_id.v_model, "review"] = change["new"]

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

            # remove the current layer
            self.map.remove_layer(cm.map.layer.current, none_ok=True)

            # unset the current_id
            self.alert_model.current_id = None

        else:

            # select the geoseries
            gdf = self.alert_model.gdf.loc[[change["new"]]]
            feat = gdf.squeeze()

            # set the alert type
            self.w_alert.v_model = cm.view.metadata.type[feat.alert]

            # read back the date in a readable format
            julian, year = math.modf(feat.date)
            julian = int(julian * 1000)
            date = datetime(int(year), 1, 1) + timedelta(days=julian - 1)
            self.w_date.v_model = date.strftime("%Y-%m-%d")

            # read the surface
            self.w_surface.v_model = feat.nb_pixel

            # get the center coordinates
            coords = list(feat.geometry.centroid.coords)[0]
            self.w_coords.v_model = f"({coords[0]:.5f}, {coords[1]:.5f})"

            # get the review value
            self.w_review.v_model = feat.review
            self.w_review.disabled = False

            # zoom the map on the geometry
            self.map.zoom_bounds(feat.geometry.bounds)
            self.map.zoom = min(16, self.map.zoom)

            # display the alert in warning color
            self.map.remove_layer(cm.map.layer.current, none_ok=True)
            layer = GeoJSON(
                data=gdf.__geo_interface__,
                style=cp.current_alert_style,
                name=cm.map.layer.current,
            )
            self.map.add_layer(layer)

            # change the id in the model
            # to trigger the other processes
            self.alert_model.current_id = change["new"]

            return

    def _on_alerts_change(self, change):

        self.w_id.v_model = None

        if self.alert_model.gdf is None:
            return

        # update the dynamic select
        id_list = self.alert_model.gdf.id.tolist()
        self.w_id.set_items(id_list)

        # unable the export btns
        self.btn_csv.disabled = False
        self.btn_gpkg.disabled = False
        self.btn_kml.disabled = False

        # show the table
        self.show()

        return self

    @su.switch("loading", "disabled", on_widgets=["btn_csv", "btn_gpkg", "btn_kml"])
    def export(self, widget, event, data):
        """export the file to multple formats"""

        gdf = self.alert_model.gdf.copy()

        # create the name
        name = f"{self.aoi_model.name}_{self.alert_model.start}_{self.alert_model.end}_{self.alert_model.min_size}"

        # identify the format
        format_ = widget.attributes["data"]
        path = cp.result_dir / f"{name}.{format_}"

        if format_ == "csv":

            # add the lat and long column
            gdf["lat"] = gdf.apply(
                lambda r: list(r.geometry.centroid.coords)[0][0], axis=1
            )
            gdf["lng"] = gdf.apply(
                lambda r: list(r.geometry.centroid.coords)[0][1], axis=1
            )

            # remove the geometries
            df = pd.DataFrame(gdf.drop(columns="geometry"))

            # export the file
            df.to_csv(path, index=False)

        elif format_ in ["gpkg", "kml"]:

            # allow the kml driver in fiona
            fiona.supported_drivers["KML"] = "rw"

            # export the file
            with fiona.drivers():
                gdf.to_file(path, layer=cm.map.layer.alerts, driver=format_.upper())

        self.alert.add_msg(cm.view.metadata.export.format(path), "success")

        return

    @staticmethod
    def row(header, widget):
        """wrapper function to create a row from a header and a widget"""

        th = sw.Html(tag="th", children=[header])
        td = sw.Html(tag="td", children=[widget])
        tr = sw.Html(tag="tr", children=[th, td])

        return tr


class MetadataControl(sm.MenuControl):
    def __init__(self, alert_model, map_, aoi_model):

        # define the view
        self.view = MetadataView(alert_model, map_, aoi_model)

        # create the control
        super().__init__("fas fa-info", self.view, m=map_, position="topleft")