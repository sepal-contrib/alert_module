from sepal_ui import sepalwidgets as sw


class Btn(sw.Btn):
    def set_txt(self, txt):
        """set the txt of the btn dynamically"""

        children = self.children.copy()
        self.children = [children[0], txt]

        return
