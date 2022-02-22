from datetime import timedelta, date
from json import dumps

from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su

from component import parameter as cp
from component import widget as cw
from component import model as cm


class AlertView(sw.Card):
    def __init__(self, aoi_model):

        # init the models
        self.alert_model = cm.AlertModel()
        self.aoi_model = aoi_model

        # select the alert collection that will be used
        self.w_alert = sw.Select(
            v_model=None, items=[*cp.alert_drivers], label="alert collection"
        )

        # select the type of alert to use in the computation
        # recent will be defined from now - X days in the past
        # historical will provide 2 date pickers
        self.w_alert_type = sw.RadioGroup(
            label="type of alerts",
            v_model=self.alert_model.alert_type,
            row=True,
            children=[
                sw.Radio(label="recente", value="RECENT"),
                sw.Radio(label="Historical", value="HISTORICAL"),
            ],
        )

        # dropdown to select the lenght of the "recent" period
        self.w_recent = sw.Select(
            v_model=None, items=cp.time_delta, label="In the last"
        )

        # create a datepickers row to select the 2 historical dates
        self.w_historic = cw.DateLine().disable().hide()

        # select the minimal size of the alerts
        self.w_size = cw.SurfaceSelect()

        # set a btn to validate and load the alerts
        self.btn = sw.Btn("select Alerts")

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
        )

        super().__init__(
            children=[
                self.w_alert,
                self.w_alert_type,
                self.w_recent,
                self.w_historic,
                self.w_size,
                self.btn,
                self.alert,
            ],
            class_="mt-5",
        )

        # add js behaviours
        self.w_alert_type.observe(self._change_alert_type, "v_model")
        self.w_alert.observe(self._set_alert_collection, "v_model")
        self.w_recent.observe(self._set_recent_period, "v_model")
        self.btn.on_event("click", self.load_alerts)

    @su.loading_button(debug=True)
    def load_alerts(self, widget, event, data):
        """load the alerts in the model"""

        # check that all variables are set
        if not all(
            [
                self.alert.check_input(
                    self.aoi_model.feature_collection, "select an aoi first"
                ),
                self.alert.check_input(
                    self.alert_model.alert_collection, "select alert collection"
                ),
                self.alert.check_input(
                    self.alert_model.alert_type, "select an alert type"
                ),
                self.alert.check_input(
                    self.alert_model.start, "select a start for the alerts"
                ),
                self.alert.check_input(
                    self.alert_model.end, "select an end for the alerts"
                ),
                self.alert.check_input(
                    self.alert_model.min_size, "select a minimal size"
                ),
            ]
        ):
            return

        self.alert.add_msg(self.aoi_model.name)
        # self.alert.add_live_msg(dumps(self.alert_model.export_data()))

        return self

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

        # init the datepicker with appropriate min and max values
        year_list = cp.alert_drivers[change["new"]]["avalaible_years"]
        self.w_historic.init(min(year_list), max(year_list))

        # unable it
        self.w_historic.unable()

        return self

    def _change_alert_type(self, change):
        """change how the end user select the time period"""

        # delete all previous values
        self.w_recent.reset()
        self.w_historic.w_start.reset()
        self.w_historic.w_end.reset()

        # exchange component visibility
        self.w_historic.toggle_viz()
        self.w_recent.toggle_viz()

        return self