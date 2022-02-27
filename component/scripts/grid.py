from itertools import product

from shapely import geometry as sg
from shapely.ops import unary_union
import geopandas as gpd
import numpy as np
import ee


def set_grid(aoi_gdf):
    """
    compute a grid around a given aoi (ee.FeatureCollection) that is fit for alert extraction
    The grid cells are tailored to be adapted to always run without timeout
    """

    # set the grid cell size in degree
    size = 0.1

    # retreive the bounding box
    aoi_bb = sg.box(*aoi_gdf.total_bounds)
    min_x, min_y, max_x, max_y = aoi_bb.bounds

    # create numpy corrdinates table
    longitudes = np.concatenate([np.arange(min_x, max_x, size), [max_x]])
    lattitudes = np.concatenate([np.arange(min_y, max_y, size), [max_y]])

    # filter with the geometry bounds
    min_lon, min_lat, max_lon, max_lat = aoi_gdf.total_bounds

    # create the grid
    names, squares = [], []
    for ix, iy in product(range(len(longitudes) - 1), range(len(lattitudes) - 1)):

        # fill the grid values
        names.append(f"{longitudes[ix]:.4f}E-{lattitudes[iy]:.4f}N")
        squares.append(
            sg.box(
                longitudes[ix],
                lattitudes[iy],
                longitudes[ix + 1],
                lattitudes[iy + 1],
            )
        )

    # create a buffer grid in lat-long
    grid = gpd.GeoDataFrame(
        {"names": names, "geometry": squares}, crs="EPSG:4326"
    ).intersection(aoi_gdf.dissolve()["geometry"][0])

    # filter out empty geometries
    grid = grid[np.invert(grid.is_empty)]

    return grid
