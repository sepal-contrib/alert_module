from datetime import datetime
import time
from pathlib import Path

import rasterio as rio
from rasterio.merge import merge

from component.scripts import glad_import
from component.scripts import gee_import
from component.scripts import radd_import
from component.scripts import gdrive
from component.scripts import gee
from component.message import cm
from component import parameter as cp


def get_alerts(aoi_model, model, alert):

    alerts = {
        "GEE": get_gee_assets,
        "LOCAL": get_local_alerts,
        "GLAD": get_glad_alerts,
        "RADD": get_radd_alerts,
    }

    return alerts[model.alert_type](aoi_model, model, alert)


def get_glad_alerts(aoi_model, model, alert):

    # verify useful inputs
    if not alert.check_input(model.start):
        return (None, None)
    if not alert.check_input(model.end):
        return (None, None)

    # convert to dates
    start = datetime.strptime(model.start, "%Y-%m-%d")
    end = datetime.strptime(model.end, "%Y-%m-%d")

    # check that the year is not prior to 2017
    if start.year < 2017:
        alert.add_live_msg(cm.driver.too_early, "error")
        return (None, None)

    # verify the dates are in the same year
    if start.year != end.year:
        alert.add_live_msg(cm.driver.wrong_year, "error")
        return (None, None)

    year = start.year

    # filename
    aoi_name = aoi_model.name
    filename = aoi_name + f"_{model.start}_{model.end}_glad_alerts"

    # check if the file exist
    result_dir = cp.create_result_folder(aoi_model)

    basename = f"{aoi_name}_{model.start}_{model.end}_glad"
    alert_date_tmp_map = result_dir / f"{basename}_tmp_date.tif"
    alert_date_map = result_dir / f"{basename}_date.tif"
    alert_tmp_map = result_dir / f"{basename}_tmp_map.tif"
    alert_raw_map = result_dir / f"{basename}_raw_map.tif"
    alert_map = result_dir / f"{basename}_map.tif"

    if alert_tmp_map.is_file() or alert_map.is_file():
        alert.add_live_msg(cm.sepal.already_done, "success")
        return (alert_date_tmp_map, alert_tmp_map)

    drive_handler = gdrive.gdrive()

    # check for the julian day task
    filename_date = f"{filename}_dates"
    alerts_date = glad_import.get_alerts_dates(
        aoi_model.feature_collection, year, [start, end]
    )
    download = drive_handler.download_to_disk(
        filename_date, alerts_date, aoi_model, alert
    )

    # reteive alert date masked with date range
    filename_map = f"{filename}_map"
    alerts = glad_import.get_alerts(aoi_model.feature_collection, year, alerts_date)
    download = drive_handler.download_to_disk(filename_map, alerts, aoi_model, alert)

    # wait for completion
    # I assume that there is 2 or 0 file to launch
    # if one of the 2 process have been launch individually it will crash
    if download:
        gee.custom_wait_for_completion([filename_map, filename_date], alert)
        alert.add_live_msg(cm.driver.task_completed.format(filename_map), "success")

    # merge and compress them
    digest_tiles(filename_date, result_dir, alert, alert_date_tmp_map)
    digest_tiles(filename_map, result_dir, alert, alert_tmp_map)

    # remove the files from gdrive
    drive_handler.delete_files(drive_handler.get_files(filename_date))
    drive_handler.delete_files(drive_handler.get_files(filename_map))

    alert.add_live_msg(cm.sepal.computation_completed, "success")

    # return the obtained files
    return (alert_date_tmp_map, alert_tmp_map)


def get_radd_alerts(aoi_model, model, alert):

    # verify useful inputs
    if not alert.check_input(model.start):
        return (None, None)
    if not alert.check_input(model.end):
        return (None, None)

    # convert to dates
    start = datetime.strptime(model.start, "%Y-%m-%d")
    end = datetime.strptime(model.end, "%Y-%m-%d")

    # check that the year is not prior to 2019
    if start.year < 2019:
        alert.add_live_msg(cm.driver.radd_too_early, "error")
        return (None, None)

    # filename
    aoi_name = aoi_model.name
    filename = aoi_name + f"_{model.start}_{model.end}_radd_alerts"

    # check if the file exist
    result_dir = cp.create_result_folder(aoi_model)

    basename = f"{aoi_name}_{model.start}_{model.end}_radd"
    alert_date_tmp_map = result_dir / f"{basename}_tmp_date.tif"
    alert_date_map = result_dir / f"{basename}_date.tif"
    alert_tmp_map = result_dir / f"{basename}_tmp_map.tif"
    alert_raw_map = result_dir / f"{basename}_raw_map.tif"
    alert_map = result_dir / f"{basename}_map.tif"

    if alert_tmp_map.is_file() or alert_map.is_file():
        alert.add_live_msg(ms.ALREADY_DONE, "success")
        return (alert_date_tmp_map, alert_tmp_map)

    drive_handler = gdrive.gdrive()

    # check for the julian day task
    filename_date = f"{filename}_dates"
    alerts_date = radd_import.get_alerts_dates(
        aoi_model.feature_collection, [start, end]
    )
    download = drive_handler.download_to_disk(
        filename_date, alerts_date, aoi_model, alert
    )

    # reteive alert date masked with date range
    filename_map = f"{filename}_map"
    alerts = radd_import.get_alerts(aoi_model.feature_collection, alerts_date)
    download = drive_handler.download_to_disk(filename_map, alerts, aoi_model, alert)

    # wait for completion
    # I assume that there is 2 or 0 file to launch
    # if one of the 2 process have been launch individually it will crash
    if download:
        gee.custom_wait_for_completion([filename_map, filename_date], alert)
        alert.add_live_msg(ms.TASK_COMPLETED.format(filename_map), "success")

    # merge and compress them
    digest_tiles(filename_date, result_dir, alert, alert_date_tmp_map)
    digest_tiles(filename_map, result_dir, alert, alert_tmp_map)

    # remove the files from gdrive
    drive_handler.delete_files(drive_handler.get_files(filename_date))
    drive_handler.delete_files(drive_handler.get_files(filename_map))

    alert.add_live_msg(cm.sepal.computation_completed, "success")

    # return the obtained files
    return (alert_date_tmp_map, alert_tmp_map)


def get_gee_assets(aoi_model, model, alert):

    # verify useful inputs
    if not alert.check_input(model.start):
        return (None, None)
    if not alert.check_input(model.end):
        return (None, None)
    if not alert.check_input(model.date_asset):
        return (None, None)
    if not alert.check_input(model.alert_asset):
        return (None, None)
    if not alert.check_input(model.asset_date_band):
        return (None, None)
    if not alert.check_input(model.asset_alerts_band):
        return (None, None)

    # check that the asset exist

    # filename
    asset_name = Path(model.alert_asset).stem
    aoi_name = aoi_model.name
    filename = f"{aoi_name}_{model.start}_{model.end}_{asset_name}_alerts"

    # check if the file exist
    result_dir = cp.create_result_folder(aoi_model)

    # convert to dates
    start = datetime.strptime(model.start, "%Y-%m-%d")
    end = datetime.strptime(model.end, "%Y-%m-%d")

    basename = f"{aoi_name}_{model.start}_{model.end}_{asset_name}"
    alert_date_tmp_map = result_dir / f"{basename}_tmp_date.tif"
    alert_date_map = result_dir / f"{basename}_date.tif"
    alert_tmp_map = result_dir / f"{basename}_tmp_map.tif"
    alert_map = result_dir / f"{basename}_map.tif"

    if alert_tmp_map.is_file():
        alert.add_live_msg(ms.ALREADY_DONE, "success")
        return (alert_date_tmp_map, alert_tmp_map)

    drive_handler = gdrive.gdrive()

    # mask the appropriate alerts
    filename_date = f"{filename}_dates"
    alerts_date = gee_import.get_alerts_dates(
        [start, end],
        aoi_model.feature_collection,
        model.date_asset,
        model.asset_date_band,
    )
    download = drive_handler.download_to_disk(
        filename_date, alerts_date.unmask(0), aoi_model, alert
    )

    # reteive alert date masked with date range
    filename_map = f"{filename}_map"
    alerts = gee_import.get_alerts(
        alerts_date,
        aoi_model.feature_collection,
        model.alert_asset,
        model.asset_alerts_band,
    )
    download = drive_handler.download_to_disk(
        filename_map, alerts.unmask(0), aoi_model, alert
    )

    # wait for completion
    # I assume that there is 2 or 0 file to launch
    # if one of the 2 process have been launch individually it will crash
    if download:
        gee.custom_wait_for_completion([filename_map, filename_date], alert)
        alert.add_live_msg(ms.TASK_COMPLETED.format(filename_map), "success")

    # merge and compress them
    digest_tiles(filename_date, result_dir, alert, alert_date_tmp_map)
    digest_tiles(filename_map, result_dir, alert, alert_tmp_map)

    # remove the files from gdrive
    drive_handler.delete_files(drive_handler.get_files(filename_date))
    drive_handler.delete_files(drive_handler.get_files(filename_map))

    alert.add_live_msg(ms.COMPUTAION_COMPLETED, "success")

    # return the obtained files
    return (alert_date_tmp_map, alert_tmp_map)


def get_local_alerts(aoi_model, model, alert):

    if not alert.check_input(model.start):
        return (None, None)
    if not alert.check_input(model.start):
        return (None, None)
    if not alert.check_input(model.date_file):
        return (None, None)
    if not alert.check_input(model.alert_file):
        return (None, None)

    # check that the file exist
    if not Path(model.date_file).is_file():
        return (None, None)
    if not Path(model.alert_file).is_file():
        return (None, None)

    # filename
    alert_name = Path(model.alert_file).stem
    aoi_name = aoi_model.name
    filename = f"{aoi_name}_{model.start}_{model.end}_{alert_name}_alerts"

    # check if the file exist
    result_dir = cp.create_result_folder(aoi_model)

    basename = f"{aoi_name}_{model.start}_{model.end}_{alert_name}"
    alert_date_map = result_dir / f"{basename}_tmp_date.tif"
    alert_map = result_dir / f"{basename}_tmp_map.tif"

    if Path(alert_map).is_file():
        alert.add_live_msg(cm.sepal.already_done, "success")
        return (alert_date_map, alert_map)

    # mask the alert dates
    start = datetime.strptime(model.start, "%Y-%m-%d").toordinal()
    end = datetime.strptime(model.end, "%Y-%m-%d").toordinal()

    with rio.open(model.date_file) as src:

        raw_data = src.read()
        out_meta = src.meta.copy()
        data = ((raw_data >= start) * (raw_data <= end)) * raw_data

        with rio.open(alert_date_map, "w", **out_meta) as dest:
            dest.write(data)

    # filter the alerts
    with rio.open(alert_date_map) as date_f, rio.open(model.alert_file) as alert_f:

        date_data = date_f.read()
        alert_data = alert_f.read()

        # I assume that they both have the same extend, res, and transform
        out_meta = date_f.meta.copy()
        out_meta.update(dtype=rio.uint8, compress="lzw")

        data = (date_data > 0) * alert_data

        with rio.open(alert_map, "w", **out_meta) as dest:
            dest.write(data.astype(rio.uint8))

    alert.add_live_msg(cm.sepal.computation_completed, "success")

    # return the obtained files
    return (alert_date_map, alert_map)


def digest_tiles(filename, result_dir, alert, tmp_file):

    drive_handler = gdrive.gdrive()
    files = drive_handler.get_files(filename)

    # if no file, it means that the download had failed
    if not len(files):
        raise Exception(cm.alert.no_files)

    drive_handler.download_files(files, result_dir)

    pathname = f"{filename}*.tif"

    files = [file for file in result_dir.glob(pathname)]

    # run the merge process
    alert.add_live_msg(cm.sepal.merge_tile)
    time.sleep(2)

    # manual open and close because I don't know how many file there are
    sources = [rio.open(file) for file in files]

    data, output_transform = merge(sources)

    out_meta = sources[0].meta.copy()
    out_meta.update(
        driver="GTiff",
        height=data.shape[1],
        width=data.shape[2],
        transform=output_transform,
        compress="lzw",
    )

    with rio.open(tmp_file, "w", **out_meta) as dest:
        dest.write(data)

    # manually close the files
    [src.close() for src in sources]

    # delete local files
    [file.unlink() for file in files]

    return
