from sepal_ui import sepalwidgets as sw
from traitlets import Bool, observe

from component.message import cm


class Chip(sw.Tooltip):
    """
    custom chip that uses the parameter of each variable from the model
    Not stand alone

    Args:
        tooltip (str): compltete text of the tooltip
        icon (str): the icon to use before the value
        unit (str): the unit
    """

    def __init__(self, value, tooltip, icon, unit):

        text = f"{value} {unit}"
        icon = sw.Icon(class_="mr-1", x_small=True, children=[icon])
        chip = sw.Chip(class_="ml-1 mr-1", x_small=True, children=[icon, text])

        super().__init__(chip, tooltip, bottom=True)


class PlanetParam(sw.ExpansionPanels):

    CHIPS = {
        # The key is the name attribute name in the model : [tooltip, icon, unit]
        "max_images": [
            cm.view.planet.advance.max_images,
            "fa-solid fa-images",
            "img",
        ],
        "days_before": [
            cm.view.planet.advance.days_before,
            "fa-solid fa-circle-arrow-left",
            "d",
        ],
        "days_after": [
            cm.view.planet.advance.days_after,
            "fa-solid fa-circle-arrow-right",
            "d",
        ],
        "cloud_cover": [cm.view.planet.advance.cloud_cover, "fa-solid fa-cloud", "%"],
    }

    disable_content = Bool(True).tag(sync=True)
    "disable trait that will decide if the widget values can be changed"

    def __init__(self, model):

        # link the alert model to adapt its values when a widget is triggered
        self.model = model

        # create a header, and display the default values
        self.title = f"{cm.view.planet.advance.title}: "
        self.header = sw.ExpansionPanelHeader()

        # set the content
        self.w_days_before = sw.NumberField(
            label=cm.view.planet.advance.days_before,
            max_=5,
            v_model=self.model.days_before,
        )

        self.w_days_after = sw.NumberField(
            label=cm.view.planet.advance.days_after,
            max_=5,
            v_model=self.model.days_after,
        )

        self.w_max_images = sw.NumberField(
            label=cm.view.planet.advance.max_images,
            max_=6,
            min_=1,
            v_model=self.model.max_images,
        )

        self.w_cloud_cover = sw.Slider(
            label=cm.view.planet.advance.cloud_cover,
            thumb_label=True,
            v_model=self.model.cloud_cover,
        )

        self.content = sw.ExpansionPanelContent(
            children=[
                self.w_max_images,
                self.w_days_before,
                self.w_days_after,
                self.w_cloud_cover,
            ]
        )

        children = [self.header, self.content]

        # shrunk the content on start
        self.shrunk()

        # set the parameters in the model
        (
            self.model.bind(self.w_days_before, "days_before")
            .bind(self.w_days_after, "days_after")
            .bind(self.w_max_images, "max_images")
            .bind(self.w_cloud_cover, "cloud_cover")
        )

        super().__init__(
            v_model=None, class_="mt-2", children=[sw.ExpansionPanel(children=children)]
        )

        # create javascript events

    def shrunk(self):
        "shrunk the content and display data in the header"

        # create chips
        chips = [Chip(getattr(self.model, k), *v) for k, v in self.CHIPS.items()]

        self.header.children = [self.title] + chips

        return

    def expand(self):
        "expand the content and remove the paramters from the header"

        self.header.children = [self.title]

        return

    @observe("v_model")
    def _on_panel_change(self, change):
        """expand or shrunk based on the change values"""

        if change["new"] == 0:
            self.expand()
        elif change["new"] is None:
            self.shrunk()

        return
