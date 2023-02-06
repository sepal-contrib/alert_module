from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
from traitlets import Bool, Int
from sepal_ui import mapping as sm
from sepal_ui import planetapi as sp

from component.message import cm
from component import widget as cw
from component import scripts as cs
from component.message import cm


class PlanetView(sw.Card):

    updated = Int(0).tag(sync=True)

    api = Bool(False).tag(sync=True)
    "wether or not to use the Planet API"

    def __init__(self, alert_model):

        # inti the model
        self.alert_model = alert_model

        # select the parameters for the planet API
        self.w_planet = sp.PlanetView()
        self.w_advance = cw.PlanetParam(self.alert_model)

        # save the planet model for simplicity
        self.model = self.w_planet.planet_model

        # set the view btn
        # cancel will cancel the use of planet data and switch to GEE based map
        # instead
        # btn is called c_btn instead of cancel to avoid duplication
        self.btn = sw.Btn(
            cm.planet_control.btn.apply,
            "fa-solid fa-check",
            color="secondary",
            small=True,
        )
        self.c_btn = sw.Btn(
            cm.planet_control.btn.cancel,
            "fa-solid fa-times",
            color="error",
            outlined=True,
            class_="mr-1",
            small=True,
        )

        # set up an alert to show information to the user
        self.alert = sw.Alert()

        # manually decorate the functions
        self.cancel = su.loading_button(self.alert, self.c_btn, True)(self.cancel)
        self.apply = su.loading_button(self.alert, self.btn, True)(self.apply)

        # create the object
        super().__init__(
            children=[
                self.w_planet,
                self.w_advance,
                sw.Row(
                    class_="mt-2 ml-1", children=[sw.Spacer(), self.c_btn, self.btn]
                ),
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

        self.alert_model.valid_key = False

        self.alert.add_msg(cm.view.planet.error.to_gee)

        return

    def apply(self, widget, event, data):
        """validate the api key"""

        # check that a level 2 key was set
        valid = False
        if "nicfi" in self.model.subscriptions:
            for p in self.model.subscriptions["nicfi"]:
                if "Level2" in p["plan"]["name"]:
                    valid = True
                    break

        # apply the paramters to the level 2 search
        self.api = valid
        self.alert_model.valid_key = valid

        # display information to the end user
        if valid is True:
            self.alert.add_msg(cm.view.planet.error.valid_key, "success")
        else:
            self.alert.add_msg(cm.view.planet.error.unvalid_key, "error")

        # send the information to the rest of the app
        self.updated += 1

        return


class PlanetControl(sm.MenuControl):
    def __init__(self, alert_model, map_):

        # create a view
        self.view = PlanetView(alert_model)
        self.view.class_list.add("ma-5")

        # integrate it in a menu
        super().__init__(
            "fa-solid fa-globe", self.view, m=map_, card_title=cm.view.setting.planet
        )
