from sepal_ui import model
from traitlets import Any


class AlertModel(model.Model):

    # input
    alert_collection = Any(None).tag(sync=True)
    alert_type = Any("RECENT").tag(sync=True)
    start = Any(None).tag(sync=True)
    end = Any(None).tag(sync=True)
    min_size = Any(0).tag(sync=True)
