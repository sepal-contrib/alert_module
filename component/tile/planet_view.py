from sepal_ui import sepalwidgets as sw
from traitlets import Bool

from component.message import cm
from component import widget as cw


class PlanetView(sw.Card):

    api = Bool(False).tag(sync=True)
    "wether or not to use the Planet API"

    def __init__(self, alert_model):

        # inti the model
        self.alert_module = alert_model

        # select the parameters for the planet API
        self.w_key = sw.PasswordField(label=cm.view.planet.key.label)
        self.w_advance = cw.PlanetParam(self.alert_module)

        super().__init__(
            children=[self.w_key, self.w_advance], class_="mt_5", elevation=False
        )
