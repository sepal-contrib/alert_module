import time
from datetime import datetime

import pandas as pd
from sepal_ui import sepalwidgets as sw
from sepal_ui import mapping as sm
from ipywidgets import Output
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba, ListedColormap
import ipyvuetify as v
import numpy as np
import rasterio as rio
from rasterio.mask import mask
from scipy import ndimage as ndi
import ee
from shapely.geometry import shape

from component import parameter as cp
from component.message import cm

#initialize earth engine
ee.Initialize()

def sepal_process(aoi_model, alert_model, alert):
    """execute the 2 different operations of the computation successively: clump and compute
    
    Args:
        aoi_model (object): the aoiIo object that contains the aoi informations
        alert_model (object): the AlertIO object that contains all the current alerts information
        alert (sw.Alert) the alert that display the alert of the process
        
    Returns:
        (str,str): the links to the .tif (res. .txt) file 
    """
        
    #define the files variables
    result_dir = cp.create_result_folder(aoi_model)
    
    #basename info are extracted from alert filename
    basename = f"{alert_model.alert.stem.replace('_tmp_map', '')}_" + "{}"
    
    alert.add_live_msg('basename: {}'.format(basename))
    time.sleep(5)
    
    clump_tmp_map      = result_dir/basename.format('tmp_clump.tif')
    clump_map          = result_dir/basename.format('clump.tif')
    alert_stats        = result_dir/basename.format('stats.txt')
    alert_stats_legacy = result_dir/basename.format('stats_legacy.txt')
    alert_date_tmp_map = result_dir/basename.format('tmp_date.tif')
    alert_date_map     = result_dir/basename.format('date.tif')
    alert_tmp_map      = result_dir/basename.format('tmp_map.tif')
    alert_map          = result_dir/basename.format('map.tif')
        
    # check that the process is not already done
    if alert_stats.is_file() and alert_stats_legacy.is_file():
        alert.add_live_msg(cm.sepal.already_done, 'success')
        return alert_stats
    
    # clump the patches together
    if not (clump_tmp_map.is_file() or clump_map.is_file()):
        alert.add_live_msg(cm.sepal.identify_patch)
        time.sleep(2)
        clump(alert_model.alert, clump_tmp_map)
    
    # cut and compress all files 
    alert.add_live_msg(cm.sepal.compress_file)
    if not alert_date_map.is_file(): cut_to_aoi(aoi_model, alert_date_tmp_map, alert_date_map)
    if not alert_map.is_file(): cut_to_aoi(aoi_model, alert_tmp_map, alert_map)
    if not clump_map.is_file(): cut_to_aoi(aoi_model, clump_tmp_map, clump_map)
    
    # create the histogram of the patches
    alert.add_live_msg(cm.sepal.patch_size)
    time.sleep(2)
    hist(alert_map, clump_map, alert_stats, alert)
    
    alert.add_live_msg(cm.sepal.computation_completed, 'success')
    
    return alert_stats

def display_results(aoi_model, alert_model, alert, stats):
    
    alert.add_live_msg(cm.sepal.display_result)
    
    aoi_name = aoi_model.name
    result_dir = cp.create_result_folder(aoi_model)
    year = datetime.strptime(alert_model.start, '%Y-%m-%d').year
    
    basename = alert_model.alert.stem.replace('_tmp_map', '')
    alert_stats = result_dir/f"{basename}_stats.txt"
    
    df = pd.read_csv(stats)
    
    # tif link
    tif_btn = sw.DownloadBtn(cm.sepal.tif_btn, result_dir/f"{basename}_map.tif")
    
    # csv file 
    alert_csv = create_csv(df, result_dir, basename, alert_model.alert_type)
    csv_btn = sw.DownloadBtn(cm.sepal.csv_btn, alert_csv)
     
    # create matplotlib hist 
    title = f'Distribution of the alerts \nfor {aoi_name} in {year}'
    fig, ax = create_fig(df, title, alert_model.alert_type)
    
    png_link = result_dir/f"{basename}_hist.png"
    fig.savefig(png_link)   # save the figure to file
    plt.close()
    png_btn = sw.DownloadBtn(cm.sepal.png_btn, png_link)
    
    # display the fig 
    out = Output()
    with plt.style.context('dark_background'):
        with out:
            fig, ax = create_fig(df, title, alert_model.alert_type)
            fig.set_facecolor((0, 0, 0, 0))
            plt.show()
    
    #mapping of the results
    m = display_alerts(aoi_model, result_dir/f"{basename}_map.tif", cp.color_palette, alert)
    
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
    
    alert.add_live_msg(cm.sepal.display_result, 'success')
    
    return children

def create_fig(df, title, alert_type):
    """useless function that create a matplotlib file because bqplot cannot yet export without a popup
    """
    
    if alert_type in ['GLAD', 'RADD']: # glad  and radd alerts
        values = {'confirmed alerts': 3, 'potential alerts': 2}
    else:
        values = {'confirmed alerts': 1}
    
    y_ = []
    max_ = 0
    for index, name in enumerate(values): 
        
        #load the patches
        y_local = df[df['value'] == values[name]]['nb_pixel'].to_numpy()
        y_local = np.append(y_local, 0) # add the 0 to prevent bugs when there are no data (2017 for ex)
        max_ = max(max_, np.amax(y_local))
        
        #add them to the global y_
        y_.append(y_local)
        
    fig, ax = plt.subplots(figsize=(10,10))
    
    ax.set_axisbelow(True)
    ax.yaxis.grid(which='both', linewidth=0.8, color='lightgrey')
    
    ax.hist(y_, label=[*values], weights=y_, color=cp.color_palette[:len(values)], bins=30, histtype='bar', stacked=True, edgecolor='black', rwidth=0.8)
    ax.set_xlim(0, max_)
    ax.legend(loc='upper right')
    ax.set_title(title, fontweight="bold")
    ax.set_yscale('log')
    ax.set_xlabel('patch size (px)')
    ax.set_ylabel('number of pixels')
    
    return (fig, ax)
    
def create_csv(df, result_dir, basename, alert_type):
    
    if alert_type in ['GLAD', 'RADD']: #glad and radd alerts
        values = {'confirmed alerts': 3, 'potential alerts': 2}
    else:
        values = {'confirmed alerts': 1}
        
    dfs = []
    for name in values:
        Y_conf = df[df['value'] == values[name]]['nb_pixel'].to_numpy()
        unique, counts = np.unique(Y_conf, return_counts=True)
        
        dfs.append(pd.DataFrame({name: counts}, index=[unique]))
    
    df2 = pd.concat(dfs, axis=1).fillna(0).T
    
    filename = result_dir/f"{basename}_distrib.csv"
    
    df2.to_csv(filename)
    
    return filename

def display_alerts(aoi_model, raster, colors, alert):
    """dipslay the selected alerts on the geemap. If the file is too big the clump will not be displayed"""
    
    # create the map
    m = sm.SepalMap(['SATELLITE', 'CartoDB.DarkMatter'])
    
    # display a raster on the map (use try pass to avoid big files problems)
    try:    
        with rio.open(raster) as f:
            min_val = int(np.amin(f.read(1)))
            max_val = int(np.amax(f.read(1)))

        # create a color map 
        color_map = []
        for i in range(min_val, max_val+1):
            if i == 3 or i == 1:
                color_map.append(list(to_rgba(colors[0])))
            elif i == 2:
                color_map.append(list(to_rgba(colors[1])))
            else:
                color_map.append([.0, .0, .0, .0])

        color_map = ListedColormap(color_map, N=max_val+1)

        m.add_raster(raster, layer_name='alerts', colormap=color_map)
    except:
        alert.add_live_msg(cm.sepal.no_display, 'warning')
    
    # Create an empty image into which to paint the features, cast to byte.
    aoi = aoi_model.feature_collection
    empty = ee.Image().byte()
    outline = empty.paint(**{'featureCollection': aoi, 'color': 1, 'width': 3})
    m.addLayer(outline, {'palette': '283593'}, 'aoi')
    m.zoom_ee_object(aoi.geometry())
    
    legend_keys = ['potential alerts', 'confirmed alerts']
    
    m.add_legend(legend_keys=legend_keys, legend_colors=colors[::-1], position='topleft')
    
    return m

def cut_to_aoi(aoi_model, tmp_file, comp_file):
    
    # create the country shape
    aoi_json = aoi_model.gdf.__geo_interface__
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
        
    tmp_file.unlink()
    
    return
 
def clump(src_f, dst_f):
    
    # define neighbours structure
    struct = ndi.generate_binary_structure(2,2)

    with rio.open(src_f) as f:
        raster = f.read(1)
        
        if np.amax(raster) == 0:
            raise Exception(cm.sepal.no_alert)
        
        # get metadata
        meta = f.meta.copy()
        shape = f.read(1).shape
        
        # identify the features 
        count = np.bincount(f.read(1).flatten())
        features = np.where(count!=0)[0]
        
        del count
        
    # init the result file 
    meta.update(dtype=np.uint8)
    with rio.open(dst_f, 'w', **meta) as f:
        f.write(np.zeros(shape, dtype=np.uint8), 1)
        
    # loop in values
    offset = 0
    for feature in features[1:]: # skip the 0
        
        # label the filtered dataset
        with rio.open(src_f) as f:
            label = ndi.label(f.read(1) == feature, structure = struct)[0]
        
        # renumber the labeled data
        label[label!=0] = offset + label[label!=0]
        
        # reduce label size to it's minimum 
        dtype = rio.dtypes.get_minimum_dtype(label)
        label = label.astype(dtype)
        
        # add the previously saved values 
        with rio.open(dst_f) as f:
            raster_labeled = f.read(1).astype(dtype)
            raster_labeled += label
            
            del label
            
        # increase the offset
        offset = np.amax(raster_labeled)
            
        # write the new data in the dst raster 
        meta.update(dtype = dtype)
        with rio.open(dst_f, 'w', **meta) as f:
            f.write(raster_labeled, 1)
            
            del raster_labeled
    
    return
    
def hist(src, mask, dst, alert):
    
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