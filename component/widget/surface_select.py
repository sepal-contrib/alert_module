from sepal_ui import sepalwidgets as sw

from component.message import cm


class SurfaceSelect(sw.TextField):
    """
    Custom Textfield to set the value of the minimal surface in Ha
    """

    def __init__(self):

        super().__init__(
            label=cm.widget.alert.surface.label,
            suffix="ha",
            v_model=0,
            class_="mb-5",
        )

        # add the js callback on the blur event
        self.on_event("blur", self._on_change)

    def _on_change(self, *args):
        """check if the new value is a numeric integer"""

        self.error_messages = None
        self.hint = ""

        if self.v_model is None:
            return

        if self.v_model.isnumeric():
            return
        else:
            # self.error = True
            self.error_messages = cm.widget.alert.surface.error
            self.v_model = 0

        return
