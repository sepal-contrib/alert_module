from sepal_ui import sepalwidgets as sw 
from sepal_ui.scripts import utils as su

from component import scripts as cs
from component.message import cm

class SepalTile(sw.Tile):
    
    def __init__(self, aoi_model, model):
        
        # gather models 
        self.aoi_model = aoi_model
        self.model = model
        
        # set the result tile
        self.result_tile = ResultTile()
        
        super().__init__(
            'sepal_tile',
            'Post Process',
            btn=sw.Btn(cm.sepal.btn),
            alert=sw.Alert(),
            inputs=[sw.Markdown(cm.sepal.process_txt)]
        )
        
        self.btn.on_event('click', self._on_click)
    
    @su.loading_button(debug=False)
    def _on_click(self, widget, event, data):
        
        # check inputs
        if not self.alert.check_input(self.aoi_model.name, cm.alert.no_aoi): return 
        if not self.alert.check_input(self.model.alert, cm.alert.no_year): return
        
        stats_link = cs.sepal_process(self.aoi_model, self.model, self.alert)
        
        if stats_link:
            # display the layout in the tile
            layout = cs.display_results(self.aoi_model, self.model, self.alert, stats_link)
            
            self.result_tile.set_content(layout)
        
        return
        
class ResultTile(sw.Tile):
    
    def __init__(self):
        
        super().__init__('result_tile', 'Results')