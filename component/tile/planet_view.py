from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
from traitlets import Bool

from component.message import cm
from component import widget as cw
from component import scripts as cs


class PlanetView(sw.Card):

    api = Bool(False).tag(sync=True)
    "wether or not to use the Planet API"

    def __init__(self, alert_model):

        # inti the model
        self.alert_model = alert_model

        # select the parameters for the planet API
        self.w_key = sw.PasswordField(label=cm.view.planet.key.label)
        self.w_advance = cw.PlanetParam(self.alert_model)

        # set the view btn
        # cancel will cancel the use of planet data and switch to GEE based map
        # instead
        # btn is called c_btn instead of cancel to avoid duplication
        self.btn = sw.Btn("apply", "fas fa-check")
        self.c_btn = sw.Btn("cancel", "fas fa-times", outlined=True, class_="mr-1")

        # set up an alert to show information to the user
        self.alert = sw.Alert()

        # bind the parameters to the model
        self.alert_model.bind(self.w_key, "api_key")

        # manually decorate the functions
        self.cancel = su.loading_button(self.alert, self.c_btn, True)(self.cancel)
        self.apply = su.loading_button(self.alert, self.btn, True)(self.apply)

        # create the object
        super().__init__(
            children=[
                self.w_key,
                self.w_advance,
                sw.Row(class_="mt-2 ml-1", children=[self.c_btn, self.btn]),
                self.alert,
            ],
            class_="mt_5",
            elevation=False,
        )

        # js bindings
        self.c_btn.on_event("click", self.cancel)
        self.btn.on_event("click", self.apply)

    def cancel(self, widget, event, data):
        """cancel the use of planet API"""

        self.alert_model.api_key = None
        self.valid_key = False

        self.alert.add_msg(cm.view.planet.error.to_gee)

        return

    def apply(self, widget, event, data):
        """validate the api key"""

        # check that a value is set for the api key
        if not self.alert.check_input(
            self.alert_model.api_key, cm.view.planet.error.no_key
        ):
            return

        # check the key
        valid = cs.is_active(self.alert_model.api_key)

        # set the valid value in the model
        self.alert_model.valid_key = valid

        # display information to the end user
        msg = (
            cm.view.planet.error.valid_key
            if valid is True
            else cm.view.planet.error.unvalid_key
        )
        type_ = "success" if valid is True else "error"
        self.alert.add_msg(msg, type_)

        return
