import time
import glob
import os
from pathlib import Path
from datetime import datetime
import itertools

import ee
import ipyvuetify as v
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import rasterio as rio
from rasterio.warp import calculate_default_transform
from rasterio.mask import mask
from scipy import ndimage as ndi
from sepal_ui import mapping as sm
from sepal_ui import sepalwidgets as sw
from shapely.geometry import shape
import geemap
from ipywidgets import Output

from utils import utils
from utils import messages as ms
from utils import parameters as pm
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
    result_dir = utils.create_result_folder(aoi_io)
    
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
    if not (os.path.isfile(clump_tmp_map) or os.path.isfile(clump_map)):
        output.add_live_msg(ms.IDENTIFY_PATCH)
        time.sleep(2)
        clump(alert_io.alert, clump_tmp_map)
    
    #cut and compress all files 
    output.add_live_msg(ms.COMPRESS_FILE)
    if not os.path.isfile(alert_date_map): cut_to_aoi(aoi_io, alert_date_tmp_map, alert_date_map)
    if not os.path.isfile(alert_map): cut_to_aoi(aoi_io, alert_tmp_map, alert_map)
    if not os.path.isfile(clump_map): cut_to_aoi(aoi_io, clump_tmp_map, clump_map)
    
    #create the histogram of the patches
    output.add_live_msg(ms.PATCH_SIZE)
    time.sleep(2)
    hist(alert_map, clump_map, alert_stats, output)
    
    output.add_live_msg(ms.COMPUTAION_COMPLETED, 'success')
    
    return alert_stats

def display_results(aoi_io, alert_io, output, stats):
    
    output.add_live_msg(ms.DISPLAY_RESULT)
    
    aoi_name = aoi_io.get_aoi_name()
    result_dir = utils.create_result_folder(aoi_io)
    year = datetime.strptime(alert_io.start, '%Y-%m-%d').year
    
    basename = result_dir + Path(alert_io.alert).stem.replace('_tmp_map', '')
    alert_stats = basename + '_stats.txt'
    
    df = pd.read_csv(stats)
    
    #tif link
    tif_btn = sw.DownloadBtn(ms.TIF_BTN, basename + '_map.tif')
    
    #csv file 
    alert_csv = create_csv(df, basename, alert_io.alert_type)
    csv_btn = sw.DownloadBtn(ms.CSV_BTN, alert_csv)
     
    #create matplotlib hist 
    title = f'Distribution of the alerts \nfor {aoi_name} in {year}'
    fig, ax = create_fig(df, title, alert_io.alert_type)
    
    png_link = f'{basename}_hist.png'
    fig.savefig(png_link)   # save the figure to file
    plt.close()
    png_btn = sw.DownloadBtn(ms.PNG_BTN, png_link)
    
    #display the fig 
    out = Output()
    with plt.style.context('dark_background'):
        with out:
            fig, ax = create_fig(df, title, alert_io.alert_type)
            fig.set_facecolor((0, 0, 0, 0))
            plt.show()
    
    #mapping of the results
    m = display_alerts(aoi_io, basename + '_map.tif', pm.getPalette())
    
    ################################
    ##   create a sum-up layout   ##
    ################################
    
    #create the partial layout 
    partial_layout = v.Layout(
        Row=True,
        align_center=True,
        class_='pa-0 mt-5', 
        children=[
            v.Flex(xs12=True, md6=True, class_='pa-0', children=[out]),
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
    
    output.add_live_msg(ms.DISPLAY_RESULT, 'success')
    
    return children

def create_fig(df, title, alert_type):
    """useless function that create a matplotlib file because bqplot cannot yet export without a popup
    """
    
    if alert_type == available_drivers[2]: #glad alerts
        values = {'confirmed alerts': 3, 'potential alerts': 2}
    else:
        values = {'confirmed alerts': 1}
    
    y_ = []
    max_ = 0
    for index, name in enumerate(values): 
        
        #load the patches
        y_local = df[df['value'] == values[name]]['nb_pixel'].to_numpy()
        y_local = np.append(y_local, 0) #add the 0 to prevent bugs when there are no data (2017 for ex)
        max_ = max(max_, np.amax(y_local))
        
        #add them to the global y_
        y_.append(y_local)
        
    fig, ax = plt.subplots(figsize=(10,10))
    
    ax.set_axisbelow(True)
    ax.yaxis.grid(which='both', linewidth=0.8, color='lightgrey')
    
    ax.hist(y_, label=[*values], weights=y_, color=pm.getPalette()[:len(values)], bins=30, histtype='bar', stacked=True, edgecolor='black', rwidth=0.8)
    ax.set_xlim(0, max_)
    ax.legend(loc='upper right')
    ax.set_title(title, fontweight="bold")
    ax.set_yscale('log')
    ax.set_xlabel('patch size (px)')
    ax.set_ylabel('number of pixels')
    
    return (fig, ax)
    
def create_csv(df, basename, alert_type):
    
    if alert_type == available_drivers[2]: #glad alerts
        values = {'confirmed alerts': 3, 'potential alerts': 2}
    else:
        values = {'confirmed alerts': 1}
        
    dfs = []
    for name in values:
        Y_conf = df[df['value'] == values[name]]['nb_pixel'].to_numpy()
        unique, counts = np.unique(Y_conf, return_counts=True)
        
        dfs.append(pd.DataFrame({name: counts}, index=[unique]))
    
    df2 = pd.concat(dfs, axis=1).fillna(0).T
    
    filename = basename + '_distrib.csv'
    
    df2.to_csv(filename)
    
    return filename

def display_alerts(aoi_io, raster, colors):
    """dipslay the selected alerts on the geemap
    currently re-computing the alerts on the fly because geemap is faster to use ee interface than reading a .tif file
    """
    
    #create the map
    m = sm.SepalMap(['SATELLITE', 'CartoDB.DarkMatter'])
    
    #display a raster on the map (use try pass to avoid big files problems)
    try:
        m.add_raster(raster, layer_name='alerts', opacity=.7)
    except:
        pass
    
    #Create an empty image into which to paint the features, cast to byte.
    aoi = aoi_io.get_aoi_ee()
    empty = ee.Image().byte()
    outline = empty.paint(**{'featureCollection': aoi, 'color': 1, 'width': 3})
    m.addLayer(outline, {'palette': '283593'}, 'aoi')
    m.zoom_ee_object(aoi.geometry())
    
    
    #TODO check the legend 
    legend_keys = ['potential alerts', 'confirmed alerts']
    legend_colors = colors[::-1]
    
    m.add_legend(legend_keys=legend_keys, legend_colors=legend_colors, position='topleft')
    
    return m

def cut_to_aoi(aoi_io, tmp_file, comp_file):
    
    # create the country shape
    aoi_json = geemap.ee_to_geojson(aoi_io.get_aoi_ee())
    aoi_features = aoi_json['features']
    aoi_shp = [shape(aoi_features[i]['geometry']) for i in range(len(aoi_features))]
    
    with rio.open(tmp_file) as src:
        
        out_image, out_transform = mask(src, aoi_shp, all_touched=True)
    
        # compress the image in the best possible dtype
        dtype = rio.dtypes.get_minimum_dtype(out_image)
        out_image = out_image.astype(dtype)
    
        out_meta = src.meta.copy()
        out_meta.update(
            dtype = dtype,
            driver = 'GTiff',
            height = out_image.shape[1],
            width = out_image.shape[2],
            transform = out_transform,
            compress='lzw'
        )
    
        with rio.open(comp_file, "w", **out_meta) as dest:
            dest.write(out_image)
        
    os.remove(tmp_file)
    
    return
 
def clump(src_f, dst_f):
    
    # define neighbours structure
    struct = ndi.generate_binary_structure(2,2)

    with rio.open(src_f) as f:
        
        raster = f.read(1)
        meta = f.meta.copy()
        raster = raster.astype(np.int8)
        
    raster_labeled = ndi.label(raster, structure = struct)[0]
    
    # free the memory occupied by the raster 
    del raster
    
    # change the dtype of the destination file
    dtype = rio.dtypes.get_minimum_dtype(raster_labeled)
    raster_labeled = raster_labeled.astype(dtype)
    meta.update(dtype = dtype)
                         
    # write the file in the tmp clump
    with rio.open(dst_f, 'w', **meta) as dst:
        dst.write(raster_labeled, 1)
    
    return
    
def hist(src, mask, dst, output):
    
    # identify the clumps
    with rio.open(mask) as f:
        mask_raster_flat = f.read(1).flatten()

    num_features = np.max(mask_raster_flat)
    count = np.bincount(mask_raster_flat, minlength = num_features + 1)
    
    del mask_raster_flat
        
    # identify the value
    with rio.open(src) as f_src, rio.open(mask) as f_mask:
        src_raster = f_src.read(1)
        mask_raster = f_mask.read(1)

    values = np.zeros(num_features + 1, dtype=src_raster.dtype)
    values[mask_raster] = src_raster
    
    # free memory
    del mask_raster
    del src_raster
    
    # create the patchId list
    index = [i for i in range(num_features + 1)]
    
    df = pd.DataFrame({'patchId': index, 'nb_pixel': count, 'value': values})

    # remove 255 and 0 (no-alert value)
    df = df[(df['value'] != 255) & (df['value'] != 0)]
        
    df.to_csv(dst, index=False)
        
    return