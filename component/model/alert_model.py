from sepal_ui import model
from traitlets import Any


class AlertModel(model.Model):

    # input
    alert_type = Any(None).tag(sync=True)
    start = Any(None).tag(sync=True)
    end = Any(None).tag(sync=True)
    date_file = Any(None).tag(sync=True)
    alert_file = Any(None).tag(sync=True)
    date_asset = Any(None).tag(sync=True)
    alert_asset = Any(None).tag(sync=True)
    asset_date_band = Any(None).tag(sync=True)
    asset_alerts_band = Any(None).tag(sync=True)

    # output
    date = Any(None).tag(sync=True)
    alert = Any(None).tag(sync=True)
