from datetime import timedelta, date, datetime
from json import dumps
import time

import ee
from pathlib import Path
import geopandas as gpd
from ipyleaflet import GeoJSON

from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
from sepal_ui import color as sc

import ee

from component import parameter as cp
from component import widget as cw
from component.model import AlertModel
from component import scripts as cs
from component.message import cm


class AlertView(sw.Card):
    def __init__(self, aoi_model, map_):

        # init the models
        self.alert_model = AlertModel()
        self.aoi_model = aoi_model

        # wire the map object
        self.map = map_

        # select the alert collection that will be used
        self.w_alert = sw.Select(
            v_model=None,
            items=[*cp.alert_drivers],
            label=cm.view.alert.collection.label,
        )

        # select the type of alert to use in the computation
        # recent will be defined from now - X days in the past
        # historical will provide 2 date pickers
        self.w_alert_type = sw.RadioGroup(
            label=cm.view.alert.type.label,
            v_model=self.alert_model.alert_type,
            row=True,
            children=[
                sw.Radio(label=cm.view.alert.type.recent, value="RECENT"),
                sw.Radio(label=cm.view.alert.type.custom, value="HISTORICAL"),
            ],
        )

        # add the specific assetSelect for other types of alerts
        # hidden by default
        self.w_asset = sw.AssetSelect(
            label=cm.view.alert.asset.label, types=["IMAGE"]
        ).hide()

        # dropdown to select the lenght of the "recent" period
        self.w_recent = sw.Select(
            v_model=None, items=cp.time_delta, label=cm.view.alert.recent.label
        ).hide()

        # create a datepickers row to select the 2 historical dates
        self.w_historic = cw.DateLine().hide()

        # select the minimal size of the alerts
        self.w_size = cw.SurfaceSelect()

        # set a btn to validate and load the alerts
        self.btn = sw.Btn(cm.view.alert.btn.label)

        # set an alert to display information to the end user
        self.alert = sw.Alert()

        # bind the widgets and the model
        # w_recent binding will be done manually
        (
            self.alert_model.bind(self.w_alert, "alert_collection")
            .bind(self.w_alert_type, "alert_type")
            .bind(self.w_historic.w_start, "start")
            .bind(self.w_historic.w_end, "end")
            .bind(self.w_size, "min_size")
            .bind(self.w_asset, "asset")
        )

        super().__init__(
            children=[
                self.w_alert,
                self.w_asset,
                self.w_alert_type,
                self.w_recent,
                self.w_historic,
                self.w_size,
                self.btn,
                self.alert,
            ],
            class_="mt-5",
            elevation=False,
        )

        # add js behaviours
        self.w_alert_type.observe(self._change_alert_type, "v_model")
        self.w_alert.observe(self._set_alert_collection, "v_model")
        self.w_recent.observe(self._set_recent_period, "v_model")
        self.btn.on_event("click", self.load_alerts)
        self.aoi_model.observe(self.remove_alerts, "name")
        self.w_asset.observe(self.set_period, "v_model")
        self.w_alert.observe(self.display_spatial_extent, "v_model")
        self.w_asset.observe(self.display_spatial_extent, "v_model")

    def remove_alerts(self, change):
        """
        remove the alerts on name change i.e. aoi change
        The other clearing methods are trigger by the metadata and the planet tile
        """

        self.map.remove_layername("alerts")

        return

    @su.loading_button(debug=True)
    def load_alerts(self, widget, event, data):
        """load the alerts in the model"""

        # check that all variables are set
        su.check_input(self.aoi_model.feature_collection, cm.view.alert.error.no_aoi)
        su.check_input(
            self.alert_model.alert_collection, cm.view.alert.error.no_collection
        )
        su.check_input(self.alert_model.alert_type, cm.view.alert.error.no_type)
        su.check_input(self.alert_model.start, cm.view.alert.error.no_start)
        su.check_input(self.alert_model.end, cm.view.alert.error.no_end)
        su.check_input(self.alert_model.min_size, cm.view.alert.error.no_size)

        # clean the current display if necessary
        self.alert_model.current_id = None
        self.map.remove_layername(cm.map.layer.alerts)

        # create the grid
        grid = cs.set_grid(self.aoi_model.gdf)

        # loop in the grid to avoid timeout in the define AOI
        # display information to the user
        self.alert.reset().show()
        self.alert.update_progress(0)
        data = None
        for i, geom in enumerate(grid.geometry):

            ee_geom = ee.FeatureCollection(ee.Geometry(geom.__geo_interface__))

            # load the alerts in the system
            all_alerts = cs.get_alerts(
                collection=self.alert_model.alert_collection,
                start=self.alert_model.start,
                end=self.alert_model.end,
                aoi=ee_geom,
                asset=self.alert_model.asset,
            )

            alert_clump = cs.get_alerts_clump(alerts=all_alerts, aoi=ee_geom)

            if data is None:
                data = alert_clump.getInfo()
            else:
                data["features"] += alert_clump.getInfo()["features"]

            self.alert.update_progress(i / len(grid))

        # save the clumps as a geoJson dict in the model
        # exit if nothing is found
        if len(data["features"]) == 0:
            raise Exception(cm.view.alert.error.no_alerts)
        else:
            gdf = gpd.GeoDataFrame.from_features(data, crs="EPSG:4326")

        # set all the values to unset
        gdf["review"] = cm.view.metadata.status.unset

        # compute the surfaces for each geometry in square meters
        gdf["surface"] = gdf.to_crs("EPSG:3857").area

        # remove the smallest alerts
        # be carefull the min offset is set in ha
        gdf = gdf[gdf.surface >= self.alert_model.min_size * 10000]

        # order the gdf by number of pixels
        gdf = gdf.sort_values(by=["nb_pixel"], ignore_index=True, ascending=False)

        # reset the ids
        gdf["id"] = gdf.index

        # save it in the model
        self.alert_model.gdf = gdf

        # add the layer on the map
        layer = self.alert_model.get_ipygeojson()
        layer.on_click(self.on_alert_click)
        self.map.add_layer(layer)

        # reset in case an error was displayed
        self.alert.reset()

        # zoom back to the aoi
        self.map.zoom_ee_object(self.aoi_model.feature_collection.geometry())

        # remove the alert bounds layer
        self.map.remove_layername("alert extend")

        return self

    def on_alert_click(self, feature, **kwargs):
        """
        change the current id on click on a specific alert feature
        This change will trigger the modification of the metadata and the map zoom
        """

        self.alert_model.current_id = feature["properties"]["id"]

        return

    def _set_recent_period(self, change):
        """
        manually set the start and end traits of the model based on the number
        of days set in the w_recent. output should be 2 string values using
        the same format as the datepickers.
        """

        # exit when it's manually set to None by the alert type change
        if change["new"] is None:
            return

        today = date.today()
        past = today - timedelta(days=change["new"])

        self.alert_model.start = today.strftime("%Y-%m-%d")
        self.alert_model.end = past.strftime("%Y-%m-%d")

        return self

    def _set_alert_collection(self, change):
        """set the min and max year based on the selected data collection"""

        # empty and hide the component by default
        self.w_alert_type.show()
        self.w_asset.reset()
        self.w_asset.hide()

        # if nrt system is set I need to show the asset select widget first
        # the datepicker is discarded as the information won't be needed
        if change["new"] in ["NRT", "CUSUM"]:
            self.w_asset.show()
            self.w_historic.hide()
            self.w_recent.hide()
            self.w_alert_type.hide()

        # init the datepicker with appropriate min and max values
        elif change["new"] in ["RADD", "GLAD-L", "GLAD-S"]:
            year_list = cp.alert_drivers[change["new"]]["available_years"]
            self.w_alert_type.v_model = "RECENT"
            self.w_historic.init(min(year_list), max(year_list))
            self.w_recent.show()

        # glad L dataset is in maintenance for now (https://groups.google.com/g/globalforestwatch/c/v4WhGxbKG1I)
        # the issue with GLDA-L is now solved keeping this comments for later references (https://groups.google.com/g/globalforestwatch/c/nT_PSdfd3Fs)
        return self

    def _change_alert_type(self, change):
        """change how the end user select the time period"""

        # delete all previous values
        self.w_recent.reset()
        self.w_historic.w_start.reset()
        self.w_historic.w_end.reset()

        # also exit if no alert ype is selected
        if self.w_alert.v_model is None:
            return

        # change component visibility with respect to the value
        # I can't guarantee that previous visibility is hide because of NRT options
        self.w_historic.viz = self.w_alert_type.v_model == "HISTORICAL"
        self.w_recent.viz = self.w_alert_type.v_model == "RECENT"

        return

    def set_period(self, change):
        """set the time period of the historical datepicker when an asset is selected"""

        if change["new"] is None:
            return
        ########################################################################
        ##       broken for now I'll set 2022-01-01 to 2022-12-31             ##
        ########################################################################

        ## read the asset and extract the start and end timestamps
        # image = ee.Image(change["new"])
        #
        # min_ = datetime.fromtimestamp(
        #    image.get("system:time_start").getInfo() / 1000
        # ).year
        # max_ = datetime.fromtimestamp(
        #    image.get("system:time_end").getInfo() / 1000
        # ).year

        min_ = datetime.strptime("2022-01-01", "%Y-%m-%d")
        max_ = datetime.strptime("2022-12-31", "%Y-%m-%d")

        ########################################################################

        # apply it to the w_historic
        self.w_historic.init(min_, max_)
        self.w_historic.w_start.menu.children[0].v_model = min_
        self.w_historic.w_end.menu.children[0].v_model = max_
        # self.w_historic.unable()

        return

    def display_spatial_extent(self, change):
        """display the spatial extend f the selected alert system on the map"""

        # check the extent
        if self.w_alert.v_model in ["GLAD-L", "RADD"]:
            obj = ee.ImageCollection(cp.alert_drivers[self.w_alert.v_model]["asset"])
        elif self.w_alert.v_model in ["GLAD-S"]:
            obj = ee.Image(cp.alert_drivers[self.w_alert.v_model]["asset"])
        elif (
            self.w_alert.v_model in ["CUSUM", "NRT"]
            and self.w_asset.v_model is not None
        ):
            obj = ee.Image(self.w_asset.v_model)
        else:
            return

        # display it on the map
        self.map.addLayer(obj.geometry(), {"color": sc.secondary}, "alert extend")
        self.alert.add_msg(
            "check that the AOI you selected is covered by the Alert system you selected"
        )

        return
