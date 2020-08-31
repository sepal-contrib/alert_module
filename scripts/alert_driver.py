#singleton object to get the alerts images (dates and alerts)
from utils import messages as ms 
import ipyvuetify as v
from ipywidgets import jslink
from sepal_ui import sepalwidgets as sw
import glob
import os
from functools import partial

available_drivers = [
    'gee_assets',
    'local_files',
    'glad_alerts'
]
class DatePicker(v.Layout, sw.SepalWidget):
    
    def __init__(self, label="Date", **kwargs):
        
        date_picker = v.DatePicker(
            no_title=True, 
            v_model=None, 
            scrollable=True
        )

        date_text =  v.TextField(
            v_model=None,
            label=label,
            hint="YYYY-MM-DD format",
            persistent_hint=True, 
            prepend_icon="event",
            readonly=True,
            v_on='menuData.on'
        )

        menu = v.Menu(
            transition="scale-transition",
            offset_y=True,       
            v_slots=[{
                'name': 'activator',
                'variable': 'menuData',
                'children': date_text,
            }], 
            children=[date_picker]
        )

        super().__init__(
            v_model=None,
            row=True,
            class_='pa-5',
            align_center=True,
            children=[v.Flex(xs10=True, children=[menu])],
            **kwargs
        )

        jslink((date_picker, 'v_model'), (date_text, 'v_model'))
        jslink((date_picker, 'v_model'), (self, 'v_model'))


class AlertIo:
    
    def __init__(self):
        # input
        self.alert_type = None
        self.start = None
        self.end = None
        self.date_file = None
        self.alert_file = None
        self.date_asset = None
        self.alert_asset = None
        
        # output 
        self.date = None
        self.alert = None
        
# tile class of the driver 
class DriverTile(sw.Tile):
    
    def __init__(self, io, **kwargs):
        self.io = io
        
        self.btn = sw.Btn(ms.SELECT_ALERTS, 'mdi-map-marker-check')
        self.output = sw.Alert()
        
        
        # create the inputs 
        self.set_inputs()
        inputs = [
            self.select_type,
            self.picker_line,
            self.select_date_file,
            self.select_alerts_file,
            self.select_date_asset,
            self.select_alerts_asset
        ]
         
        # hide all inputs but select_type
        self.show_inputs()
        
        
        # misc
        id_ = "driver_widget"
        title = "Select your alerts"
        
        super().__init__(
                id_,
                title,
                btn=self.btn,
                output=self.output,
                inputs=inputs,
                **kwargs
        )
        
    def set_inputs (self):
        
        root_dir = os.path.expanduser('~')
        
        # select type 
        self.select_type = v.Select(items=available_drivers, label=ms.SELECT_TYPE, v_model=None)
        #self.output.bind(self.select_type, self.io, 'alert_type')
        
        # start/end line
        self.start_picker = DatePicker('Start', xs6=True)
        self.output.bind(self.start_picker.children[0].children[0].children[0], self.io, 'start')
        
        self.end_picker = DatePicker('End', xs6=True)
        self.output.bind(self.end_picker.children[0].children[0].children[0], self.io, 'end')
        
        self.picker_line = v.Layout(xs=12, row=True,  children=[self.start_picker, self.end_picker])
        
        # date file
        raw_list = glob.glob(root_dir + "/**/*.tif*", recursive=True)
        self.select_date_file = v.Select(items=raw_list, label=ms.SELECT_DATE_FILE, v_model=None)
        self.output.bind(self.select_date_file, self.io, 'date_file')
        
        # alert file 
        self.select_alerts_file = v.Select(items=raw_list, label=ms.SELECT_ALERTS_FILE, v_model=None)
        self.output.bind(self.select_alerts_file, self.io, 'alert_file')
        
        # date asset
        self.select_date_asset = v.TextField(label=ms.SELECT_DATE_ASSET, placeholder='users/[username]/[asset_name]', v_model=None)
        self.output.bind(self.select_date_asset, self.io, 'date_asset')
        
        # alert asset 
        self.select_alerts_asset = v.TextField(label=ms.SELECT_ALERTS_ASSET, placeholder='users/[username]/[asset_name]', v_model=None)
        self.output.bind(self.select_alerts_asset, self.io, 'alert_asset')
        
        return self
    
    def show_inputs(self):
        
        #hide them all but select_type
        inputs_list = [self.picker_line, self.select_date_file, self.select_alerts_file, self.select_date_asset, self.select_alerts_asset]
        self.toggle_inputs([], inputs_list)
        
        def on_change(widget, data, event, inputs_list, obj):
            base_list = [obj.picker_line] # the date pickers are used for every type of alerts
            
            setattr(obj.io, 'alert_type', widget.v_model)
            
            if widget.v_model == available_drivers[0]: # gee assets
                fields_2_show = base_list + [obj.select_date_asset, obj.select_alerts_asset]
                obj.toggle_inputs(fields_2_show, inputs_list)
            elif widget.v_model == available_drivers[1]: #file
                fields_2_show = base_list + [obj.select_date_file, obj.select_alerts_file]
                obj.toggle_inputs(fields_2_show, inputs_list)
            elif widget.v_model == available_drivers[2]: #glad alerts
                obj.toggle_inputs(base_list, inputs_list)
            else:  # the type is not suported
                obj.toogle_inputs([], inputs_list)
            
            return 
        
        self.select_type.on_event('change', partial(
            on_change,
            inputs_list = inputs_list,
            obj = self
        ))
        
        return     
    