from sepal_ui import sepalwidgets as sw
from sepal_ui import color as sc
from ipywidgets import jslink
import ipyvuetify as v

from component.message import cm
from .map_btn import *


class DynamicSelect(sw.Layout):
    def __init__(self):

        self.prev = MapBtn("mdi-chevron-left", value=-1)
        self.next = MapBtn("mdi-chevron-right", value=1)

        self.select = sw.Select(
            dense=True,
            label=cm.dynamic_select.label,
            v_model=None,
            items=[],
            prepend_icon="mdi-pound",
            clearable=True,
        )

        super().__init__(
            v_model=None,
            align_center=True,
            row=True,
            class_="ma-1",
            children=[self.prev, self.select, self.next],
        )

        # disable by default
        self.disable()

        # js behaviour
        jslink((self, "v_model"), (self.select, "v_model"))
        self.prev.on_event("click", self._on_click)
        self.next.on_event("click", self._on_click)

    def set_items(self, items):
        """Change the value of the items of the select"""

        self.select.items = items
        self.unable()

        return self

    def _on_click(self, widget, event, data):
        """go to the next value. loop to the first or last one if we reach the end"""

        increm = widget.value

        # get the current position in the list
        val = self.select.v_model
        if val in self.select.items:
            pos = self.select.items.index(val)

            pos += increm

            # check if loop is required
            if pos == -1:
                pos = len(self.select.items) - 1
            elif pos >= len(self.select.items):
                pos = 0

        # if none was selected always start by the first
        else:
            pos = 0

        self.select.v_model = self.select.items[pos]

        return self

    def disable(self):

        self.prev.disabled = True
        self.next.disabled = True
        self.select.disabled = True

        return self

    def unable(self):

        self.prev.disabled = False
        self.next.disabled = False
        self.select.disabled = False

        return self
