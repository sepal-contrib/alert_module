from sepal_ui import sepalwidgets as sw


class DateLine(sw.Flex):
    """
    A simple layout embeding 2 datepicker with usefull methods for this module
    """

    def __init__(self):

        # create the 2 datepickers
        self.w_start = sw.DatePicker(label="start", v_model=None)
        self.w_end = sw.DatePicker(class_="ml-5", label="end", v_model=None)

        super().__init__(class_="d-flex", children=[self.w_start, self.w_end])

    def disable(self):
        """disable the datepicker"""

        self.w_start.menu.v_slots[0]["children"].disabled = True
        self.w_start.menu.children[0].min = None
        self.w_start.menu.children[0].max = None

        self.w_end.menu.v_slots[0]["children"].disabled = True
        self.w_end.menu.children[0].min = None
        self.w_end.menu.children[0].max = None

        return self

    def unable(self):
        """unable the datepicker"""

        self.w_start.menu.v_slots[0]["children"].disabled = False
        self.w_end.menu.v_slots[0]["children"].disabled = False

        return self

    def init(self, start, end):
        """when a dataset is selected dates should be selected between a min an max date"""

        # min and max are integer years
        # transform min and max into string
        # format YYYY-MM-DD
        start = f"{start}-01-01"
        end = f"{end}-12-31"

        # set it on both the datepickers
        self.w_start.menu.children[0].min = start
        self.w_start.menu.children[0].max = end

        self.w_end.menu.children[0].min = start
        self.w_end.menu.children[0].max = end

        return self
