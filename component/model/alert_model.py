from sepal_ui import model
from traitlets import Any
from ipyleaflet import GeoJSON

from component import parameter as cp


class AlertModel(model.Model):

    ############################################################################
    # input
    ############################################################################
    alert_collection = Any(None).tag(sync=True)
    "the alert collection to use as entry source, not everythin is supported"

    alert_type = Any("RECENT").tag(sync=True)
    "if the alert is using recent or historical source"

    start = Any(None).tag(sync=True)
    "the start date of the retreived alerts (YYYY-MM-DD)"

    end = Any(None).tag(sync=True)
    "the end date of the retreived alerts (YYYY-MM-DD)"

    min_size = Any(0).tag(sync=True)
    "the minimal size of an alert in ha"

    ############################################################################
    # output
    ############################################################################
    gdf = Any(None).tag(sync=True)
    "the alerts as a geopandas dataframe"

    ############################################################################
    # methods
    ############################################################################
    def get_ipygeojson(self):
        """return a ipygeojson layer ready to be displayed on the map"""

        if self.gdf is None:
            raise Exception("Impossible to load layer without he json data")

        # create a GeoJSON object
        ipygeojson = GeoJSON(
            data=self.gdf.__geo_interface__,
            style=cp.alert_style,
            hover_style={**cp.alert_style, "weight": 5},
            name="alerts",
        )

        return ipygeojson
