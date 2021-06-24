#singleton object to get the alerts images (dates and alerts)
import ipyvuetify as v
from sepal_ui import sepalwidgets as sw
from sepal_ui.scripts import utils as su
import ee 

from component import parameter as cp
from component import scripts as cs
from component.message import cm

ee.Initialize()
        
# tile class of the driver 
class DriverTile(sw.Tile):
    
    def __init__(self, model, aoi_model):
        
        # gather the models
        self.model = model
        self.aoi_model = aoi_model
        
        # select type 
        self.select_type = v.Select(items=cp.available_drivers, label=cm.driver.select_type, v_model=None)
        
        # text for each driver 
        self.local_txt = sw.Markdown(cm.alert.local).hide()
        self.gee_txt = sw.Markdown(cm.alert.gee).hide()
        self.glad_txt = sw.Markdown(cm.alert.glad).hide()
        self.radd_txt = sw.Markdown(cm.alert.radd).hide()
        
        # start/end line
        self.start_picker = sw.DatePicker('Start', xs6=True)
        self.end_picker = sw.DatePicker('End', xs6=True)
        self.picker_line = v.Layout(
            xs=12, 
            row=True,  
            children=[self.start_picker, self.end_picker], 
            class_='d-none'
        )
        
        # local files file
        self.select_date_file = sw.FileInput(['.tif', '.tiff'], label=cm.driver.select_date_file).hide()
        self.select_alerts_file = sw.FileInput(['.tif', '.tiff'], label=cm.driver.select_alerts_file).hide()
        
        # date/alert asset
        self.select_date_asset = sw.AssetSelect(xs8=True, label=cm.driver.select_date_asset, _metadata={'band': 'DATE'})
        self.select_date_asset_band = v.Select(xs4=True, class_='pl-5', label= 'band', items=None, v_model=None)
        self.asset_date_line = v.Layout(
            class_='pa-5 d-none', 
            xs12=True, 
            row=True, 
            children=[self.select_date_asset, self.select_date_asset_band], 
        )
        
        # alert asset 
        self.select_alerts_asset = sw.AssetSelect(label=cm.driver.select_alerts_asset, _metadata={'band': 'ALERT'})
        self.select_alerts_asset_band = v.Select(xs4=True, class_='pl-5', label= 'band', items=None, v_model=None)       
        self.asset_alerts_line = v.Layout(
            class_='pa-5 d-none', 
            xs12=True, 
            row=True, 
            children=[self.select_alerts_asset, self.select_alerts_asset_band]
        )
        
        # bind the widgets to the model
        self.model \
        .bind(self.select_type, 'alert_type') \
        .bind(self.start_picker, 'start') \
        .bind(self.end_picker, 'end') \
        .bind(self.select_date_file, 'date_file') \
        .bind(self.select_alerts_file, 'alert_file') \
        .bind(self.select_date_asset_band, 'asset_date_band') \
        .bind(self.select_date_asset, 'date_asset') \
        .bind(self.select_alerts_asset_band, 'asset_alerts_band') \
        .bind(self.select_alerts_asset, 'alert_asset')
        
        super().__init__(
            "driver_tile",
            "Select your alerts",
            btn=sw.Btn(cm.driver.select_alerts, 'mdi-map-marker-check'),
            alert=sw.Alert(),
            inputs=[
                self.select_type,
                self.picker_line, 
                self.radd_txt,
                self.glad_txt,
                self.local_txt, self.select_date_file, self.select_alerts_file,
                self.gee_txt, self.asset_date_line, self.asset_alerts_line
            ]
        )
        
        # add js behaviour
        self.select_date_asset.observe(self.update_asset_bands, 'v_model')
        self.select_alerts_asset.observe(self.update_asset_bands, 'v_model')
        self.select_type.observe(self.show_inputs, 'v_model')
        self.btn.on_event('click', self.process_start)
        
    def update_asset_bands(self, change):
        
        if change['owner']._metadata['band'] == 'DATE':
            dropdown = self.select_date_asset_band
        elif change['owner']._metadata['band'] == 'ALERT':
            dropdown = self.select_alerts_asset_band

        # read and add the bands to the dropdown
        ee_image = ee.ImageCollection(change['new']).first()
        dropdown.items = [band['id'] for band in ee_image.getInfo()['bands']]
            
        return
    
    def show_inputs(self, change):
        
        # all the widgets but the owner 
        inputs_list = [
            self.picker_line, 
            self.local_txt, self.select_date_file, self.select_alerts_file, 
            self.gee_txt, self.asset_date_line, self.asset_alerts_line,
            self.glad_txt, 
            self.radd_txt,
        ]
        
        base_list = [self.picker_line] # the date pickers are used for every type of alerts
            
        if change['new'] == 'GEE': # gee assets
            fields_2_show = base_list + [self.gee_txt, self.asset_date_line, self.asset_alerts_line]
        elif change['new'] == 'LOCAL': # file
            fields_2_show = base_list + [self.local_txt, self.select_date_file, self.select_alerts_file]
        elif change['new'] == 'GLAD': # glad alerts
            fields_2_show = base_list + [self.glad_txt]
        elif change['new'] == 'RADD': # radd alerts
            fields_2_show = base_list + [self.radd_txt]
        else:  # the type is not suported
            fields_2_show = []
                
        self.toggle_inputs(fields_2_show, inputs_list)
            
        return

    @su.loading_button(debug=True)
    def process_start (self, widget, event, data):
        
        self.model.date, self.model.alert = cs.get_alerts(self.aoi_model, self.model, self.alert) 
    
        return
    