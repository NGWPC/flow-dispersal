# landcover.py
import geopandas as gpd
import rasterio
import numpy as np
import warnings
from rasterstats import zonal_stats
from typing import Literal

def calculate_average_runoff_coefficient(
    tif_path: str, 
    divides_df: gpd.GeoDataFrame, 
    level: Literal['level1', 'level2'] = 'level2'
) -> gpd.GeoDataFrame:
    """
    Calculates the area-weighted average runoff coefficient for each polygon
    in a GeoDataFrame.

    The calculation can be based on either Level 1 (generalized categories) or 
    Level 2 (detailed categories) of the Anderson Land Cover Classification.

    Args:
        tif_path (str): 
            Path to the land classification TIFF file. This file is expected 
            to have discrete integer values representing land cover categories.
        divides_df (gpd.GeoDataFrame): 
            A GeoDataFrame containing the polygons for which to calculate the 
            runoff coefficient.
        level (Literal['level1', 'level2'], optional): 
            The classification level to use for runoff coefficients. 
            'level1' uses broad categories.
            'level2' uses more specific land cover types.
            Defaults to 'level2'.

    Returns:
        gpd.GeoDataFrame: 
            The input GeoDataFrame with a new column 'avg_runoff_coeff' added, 
            containing the calculated average runoff coefficient for each polygon.
            
    Raises:
        ValueError: If the 'level' argument is not 'level1' or 'level2'.
    """
    
    #  Runoff Coefficient Tables for Level 1 and Level 2
    level1_runoff_data = [
        {'Category': 'Urban', 'Codes': '21;22;23;24', 'Runoff_C': 0.875},
        {'Category': 'Agriculture', 'Codes': '71;81;82', 'Runoff_C': 0.4},
        {'Category': 'Forest', 'Codes': '41;42;43', 'Runoff_C': 0.2},
        {'Category': 'Shrubland', 'Codes': '52', 'Runoff_C': 0.175},
        {'Category': 'Barren', 'Codes': '31', 'Runoff_C': 0.075},
        {'Category': 'Wetland', 'Codes': '90;95', 'Runoff_C': 0.125},
        {'Category': 'Open Water', 'Codes': '11', 'Runoff_C': 0.95},
        {'Category': 'Perennial Ice/Snow', 'Codes': '12', 'Runoff_C': 0.90},
    ]

    level2_runoff_data = [
        {'Code': '11', 'Description': 'Open Water', 'Runoff_C': 0.95},
        {'Code': '12', 'Description': 'Perennial Ice/Snow', 'Runoff_C': 0.90},
        {'Code': '21', 'Description': 'Developed, Open Space', 'Runoff_C': 0.20},
        {'Code': '22', 'Description': 'Developed, Low Intensity', 'Runoff_C': 0.50},
        {'Code': '23', 'Description': 'Developed, Medium Intensity', 'Runoff_C': 0.75},
        {'Code': '24', 'Description': 'Developed, High Intensity', 'Runoff_C': 0.90},
        {'Code': '31', 'Description': 'Barren Land (Rock/Sand/Clay)', 'Runoff_C': 0.10},
        {'Code': '41', 'Description': 'Deciduous Forest', 'Runoff_C': 0.20},
        {'Code': '42', 'Description': 'Evergreen Forest', 'Runoff_C': 0.25},
        {'Code': '43', 'Description': 'Mixed Forest', 'Runoff_C': 0.22},
        {'Code': '52', 'Description': 'Shrub/Scrub', 'Runoff_C': 0.18},
        {'Code': '71', 'Description': 'Grassland/Herbaceous', 'Runoff_C': 0.35},
        {'Code': '81', 'Description': 'Pasture/Hay', 'Runoff_C': 0.40},
        {'Code': '82', 'Description': 'Cultivated Crops', 'Runoff_C': 0.45},
        {'Code': '90', 'Description': 'Woody Wetlands', 'Runoff_C': 0.15},
        {'Code': '95', 'Description': 'Emergent Herbaceous Wetlands', 'Runoff_C': 0.10},
    ]
    
    runoff_lookup = {}
    if level == 'level1':
        runoff_data = level1_runoff_data
        code_key = 'Codes'
    elif level == 'level2':
        runoff_data = level2_runoff_data
        code_key = 'Code'
    else:
        raise ValueError("Invalid level specified. Choose either 'level1' or 'level2'.")

    for row in runoff_data:
        codes_str = row[code_key]
        runoff_c = row['Runoff_C']
        for code in codes_str.split(';'):
            if code.strip():
                runoff_lookup[int(code.strip())] = runoff_c

    gdf = divides_df.copy()
    
    with rasterio.open(tif_path) as src:
        if src.crs != gdf.crs:
            warnings.warn(f"GeoDataFrame CRS ({gdf.crs}) does not match TIFF CRS ({src.crs}). Reprojecting GeoDataFrame.")
            gdf = gdf.to_crs(src.crs)
        nodata_val = src.nodata

    # Fetch pixel counts for each category in each polygon
    stats = zonal_stats(
        gdf,
        tif_path,
        categorical=True,
        nodata=nodata_val,
        all_touched=False  
    )

    # Calculate the weighted average
    avg_runoff_coefficients = []
    for polygon_stats in stats:
        total_weighted_runoff = 0.0
        total_pixel_count = 0

        for category_code, pixel_count in polygon_stats.items():
            runoff_c = runoff_lookup.get(category_code)
            if runoff_c is not None:
                total_weighted_runoff += pixel_count * runoff_c
                total_pixel_count += pixel_count
        
        if total_pixel_count > 0:
            avg_coeff = total_weighted_runoff / total_pixel_count
            avg_runoff_coefficients.append(avg_coeff)
        else:
            avg_runoff_coefficients.append(np.nan)

    gdf['avg_runoff_coeff'] = avg_runoff_coefficients

    return gdf