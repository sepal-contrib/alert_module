"""This file builds a custom sw.Alert widget with a new method to replace the progress bar by just counting the number of steps."""
from traitlets import Int

import sepal_ui.sepalwidgets as sw
from sepal_ui import color as sepal_color
import sepal_ui.sepalwidgets as sw


class Alert(sw.Alert):
    """Custom alert component with a new method to replace the progress bar by just counting the number of steps."""

    def __init__(self):
        super().__init__()

        # Create a count span
        self.count_span = CountSpan("Progress", with_total=True)

    def set_total(self, total):
        """Set the total value of the span"""
        self.count_span.set_total(total)

    def update_progress(self) -> None:
        """update the count span message"""

        # add the count span if not already in the children

        if self.count_span not in self.children:
            self.children = self.children + [self.count_span]

        self.count_span.update()


class CountSpan(sw.Html):
    """HTML span component to control the progress of the alert component"""

    value = Int(0).tag(sync=True)
    total = Int(0).tag(sync=True)

    def __init__(self, name, color=None, with_total=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.with_total = with_total

        # Hide the span by default
        self.hide()

        if color:
            color = getattr(sepal_color, color)
            self.style_ = f"color: {color};"

        self.tag = "p"
        self.name = name + ": "
        self.children = self.get_value()

    def get_value(self):
        """Get the value of the span"""

        if self.with_total:
            return [self.name, f"{self.value}/{self.total}"]
        return [self.name, f"{self.value}"]

    def update(self):
        """Update the value of the span"""
        self.show()
        self.value += 1
        self.children = self.get_value()

    def set_total(self, total):
        """Set the total value of the span"""
        self.total = total
        self.children = self.get_value()

    def reset(self):
        """Reset the value of the span"""

        self.value = -1
        self.total = 0
        self.update()
        self.hide()
