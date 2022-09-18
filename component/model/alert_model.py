from sepal_ui import model
from traitlets import Any
from ipyleaflet import GeoJSON

from component import parameter as cp
from component.message import cm


class AlertModel(model.Model):

    ############################################################################
    # alert input
    ############################################################################
    alert_collection = Any(None).tag(sync=True)
    "the alert collection to use as entry source, not everything is supported"

    asset = Any(None).tag(sync=True)
    "the asset of the NRT alert system only used for NRT alert collections"

    alert_type = Any("RECENT").tag(sync=True)
    "if the alert is using recent or historical source"

    start = Any(None).tag(sync=True)
    "the start date of the retreived alerts (YYYY-MM-DD)"

    end = Any(None).tag(sync=True)
    "the end date of the retreived alerts (YYYY-MM-DD)"

    min_size = Any(0).tag(sync=True)
    "the minimal size of an alert in ha"

    current_id = Any(None).tag(sync=True)
    "the id of the feature currently displayed on the map"

    ############################################################################
    # planet inputs
    ############################################################################

    valid_key = Any(False).tag(sync=True)
    "set to true if the key is validated to display alert information"

    days_before = Any(1).tag(sync=True)
    "number of days to include in the query before the requested date"

    days_after = Any(1).tag(sync=True)
    "number of days to include in the query after the requested date"

    cloud_cover = Any(20).tag(sync=True)
    "tolerated cloud coverage for the Planet imagery"

    max_images = Any(6).tag(sync=True)
    "max number of images to use for the planet mosaic"

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
            raise Exception("Impossible to load layer without the json data")

        # create a GeoJSON object
        ipygeojson = GeoJSON(
            data=self.gdf.__geo_interface__,
            style=cp.alert_style,
            hover_style={**cp.alert_style, "weight": 5},
            name=cm.map.layer.alerts,
        )

        return ipygeojson
