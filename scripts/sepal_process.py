import time
import glob
import os
from pathlib import Path
from datetime import datetime

import ee
import ipyvuetify as v
import numpy as np
from bqplot import *
import matplotlib.pyplot as plt
import gdal
import pandas as pd
from osgeo import gdalconst

from utils import utils
from utils import messages as ms
from utils import parameters as pm
from sepal_ui import mapping as sm
from sepal_ui import oft 
from sepal_ui import gdal as sgdal
from sepal_ui import sepalwidgets as sw
from scripts.alert_driver import available_drivers 

#initialize earth engine
ee.Initialize()

def sepal_process(aoi_io, alert_io, output):
    """execute the 2 different operations of the computation successively: clump and compute
    
    Args:
        aoi_io (object): the aoiIo object that contains the aoi informations
        alert_io (object): the AlertIO object that contains all the current alerts information
        output (sw.Alert) the alert that display the output of the process
        
    Returns:
        (str,str): the links to the .tif (res. .txt) file 
    """
        
    #define the files variables
    result_dir = utils.create_result_folder(aoi_io.assetId)
    
    #basename info are extracted from alert filename
    basename = Path(alert_io.alert).stem.replace('_tmp_map', '')
    
    output.add_live_msg('basename: {}'.format(basename))
    time.sleep(10)
    
    clump_tmp_map      = result_dir + basename + '_tmp_clump.tif'
    clump_map          = result_dir + basename + '_clump.tif'
    alert_stats        = result_dir + basename + '_stats.txt'
    alert_date_tmp_map = result_dir + basename + '_tmp_date.tif'
    alert_date_map     = result_dir + basename + '_date.tif'
    alert_tmp_map      = result_dir + basename + '_tmp_map.tif'
    alert_map          = result_dir + basename + '_map.tif'
        
    #check that the process is not already done
    if os.path.isfile(alert_stats):
        output.add_live_msg(ms.ALREADY_DONE, 'success')
        return alert_stats
    
    #clump the patches together
    if not os.path.isfile(clump_tmp_map):
        output.add_live_msg(ms.IDENTIFY_PATCH)
        time.sleep(2)
        oft.clump(alert_io.alert, clump_tmp_map, output=output)
    
    #cut and compress all files 
    output.add_live_msg(ms.COMPRESS_FILE)
    if not os.path.isfile(alert_date_map): cut_to_aoi(aoi_io, alert_date_tmp_map, alert_date_map)
    if not os.path.isfile(alert_map): cut_to_aoi(aoi_io, alert_tmp_map, alert_map)
    if not os.path.isfile(clump_map): cut_to_aoi(aoi_io, clump_tmp_map, clump_map)
    
    #create the histogram of the patches
    output.add_live_msg(ms.PATCH_SIZE)
    time.sleep(2)  #maxval=3 for glad alert
    io = oft.his(alert_map, alert_stats, maskfile=clump_map, maxval=3, output=output)
    
    output.add_live_msg(ms.COMPUTAION_COMPLETED, 'success')
    
    return alert_stats

def display_results(aoi_io, alert_io, output, stats):
    
    aoi_name = Path(aoi_io.assetId).stem
    result_dir = utils.create_result_folder(aoi_io.assetId)
    year = datetime.strptime(alert_io.start, '%Y-%m-%d').year
    
    basename = result_dir + Path(alert_io.alert).stem.replace('_tmp_map', '')
    alert_stats = basename + '_stats.txt'
    
    df = pd.read_csv(stats, header=None, sep=' ') 
    
    if alert_io.alert_type == available_drivers[2]: #glad alerts
        df.columns = ['patchId', 'nb_pixel', 'no_data', 'no_alerts', 'prob', 'conf']
    elif alert_io.alert_type in [available_drivers[0], available_drivers[1]]: #gee and local alerts
        df.columns = ['patchId', 'nb_pixel', 'no_data', 'no_alerts', 'conf']
    
    #tif link
    tif_btn = sw.DownloadBtn(ms.TIF_BTN, alert_io.alert)
    
    #csv file 
    alert_csv = create_csv(df, basename)
    csv_btn = sw.DownloadBtn(ms.CSV_BTN, basename + '_map.tif')
    
    
    #figs
    figs = []
    
    bins=30
    
    x_sc = LinearScale(min=1)
    y_sc = LinearScale()
    
    ax_x = Axis(label='patch size (px)', scale=x_sc)
    ax_y = Axis(label='number of pixels', scale=y_sc, orientation='vertical') 
    
    colors = pm.getPalette()

    #load the confirm patches
    y_conf = df[df['conf'] != 0]['conf'].to_numpy()
    y_conf = np.append(y_conf, 0) #add the 0 to prevent bugs when there are no data (2017 for ex)
    max_conf = np.amax(y_conf)
    
    #plot the bar chart
    conf_y, conf_x = np.histogram(y_conf, bins=30, weights=y_conf)
    bar = Bars(x=conf_x, y=conf_y, scales={'x': x_sc, 'y': y_sc}, colors=colors)
    title ='Distribution of the confirmed GLAD alerts for {0} in {1}'.format(aoi_name, year)
    
    figs.append(Figure(
        title= title,
        marks=[bar], 
        axes=[ax_x, ax_y] 
    ))
    
    labels = ['confirmed alert']
    data_hist = [y_conf]
    
    #hist
    png_link = basename + '_hist.png'
    
    title = 'Distribution of the alerts \nfor {0} in {1}'.format(aoi_name, year)
    png_link = create_png(
        data_hist, 
        labels, 
        colors, 
        bins, 
        max_conf, 
        title, 
        png_link
    )
    png_btn = sw.DownloadBtn(ms.PNG_BTN, png_link)
    
    #mapping of the results
    m = display_alerts(aoi_io.assetId, basename + '_map.tif', colors)
    
    #create a sum-up layout
    
    #create the partial layout 
    partial_layout = v.Layout(
        Row=True,
        align_center=True,
        class_='pa-0 mt-5', 
        children=[
            v.Flex(xs12=True, md6=True, class_='pa-0', children=figs),
            v.Flex(xs12=True, md6=True, class_='pa-0', children=[m])
        ]
    )
    
    #create the display
    children = [ 
        v.Layout(Row=True, children=[
            csv_btn,
            png_btn,
            tif_btn
        ]),
        partial_layout
    ]
    
    return children

def create_png(data_hist, labels, colors, bins, max_, title, filepath):
    """useless function that create a matplotlib file because bqplot cannot yet export without a popup
    """
    plt.hist(
        data_hist, 
        label=labels, 
        weights=data_hist,
        color=colors, 
        bins=bins, 
        histtype='bar', 
        stacked=True
    )
    plt.xlim(0, max_)
    plt.legend(loc='upper right')
    plt.title(title)
    plt.yscale('log')
    plt.xlabel('patch size (px)')
    plt.ylabel('number of pixels')

    plt.savefig(filepath)   # save the figure to file
    
    return filepath
    
def create_csv(df, basename):
    
    Y_conf = df[df['conf'] != 0]['conf'].to_numpy()
    unique, counts = np.unique(Y_conf, return_counts=True)
    conf_dict = dict(zip(unique, counts))
    
    df2 = pd.DataFrame([conf_dict], index=['confirmed alerts'])
    
    filename = basename + '_distrib.csv'
    
    df2.to_csv(filename)
    
    return filename

def display_alerts(aoi_name, raster, colors):
    """dipslay the selected alerts on the geemap
    currently re-computing the alerts on the fly because geemap is faster to use ee interface than reading a .tif file
    """
    
    #create the map
    m = sm.SepalMap(['SATELLITE', 'CartoDB.DarkMatter'])
    
    #display a raster on the map 
    m.add_raster(raster, layer_name='alerts', opacity=.7)
    
    #Create an empty image into which to paint the features, cast to byte.
    aoi = ee.FeatureCollection(aoi_name)
    empty = ee.Image().byte()
    outline = empty.paint(**{'featureCollection': aoi, 'color': 1, 'width': 3})
    m.addLayer(outline, {'palette': '283593'}, 'aoi')
    m.zoom_ee_object(aoi.geometry())
    
    legend_keys = ['potential alerts', 'confirmed alerts']
    legend_colors = colors[::-1]
    
    m.add_legend(legend_keys=legend_keys, legend_colors=legend_colors, position='topleft')
    
    return m

def cut_to_aoi(aoi_io, tmp_file, comp_file):
    
    #cut to the aoi shape and compress
    aoi_shp = aoi_io.get_aoi_shp(utils.create_result_folder(aoi_io.assetId))
    
    options = gdal.WarpOptions(
        outputType = gdalconst.GDT_Byte,
        creationOptions = ["COMPRESS=LZW"], 
        cutlineDSName = aoi_shp,
        cropToCutline   = True
    )
    
    gdal.Warp(comp_file, tmp_file, options=options)
    os.remove(tmp_file)
    
    return
                 
    
    
    
