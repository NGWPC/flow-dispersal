# src/dataloader.py

import pandas as pd
import geopandas as gpd
from pathlib import Path

def load_all_data(
    data_path: Path,
    flowlines_file: str,
    divides_file: str,
    precipitation_file: str,
    ksat_file: str,
    outlet_discharge_file: str,
    manning_params_file: str = None
) -> tuple:
    """
    Loads all necessary data files for the discharge disaggregation workflow.

    It reads a mix of GeoPackage and Parquet files from the specified data directory.

    Args:
        data_path (Path): The path to the data directory.
        flowlines_file (str): Filename of the flowlines GeoPackage.
        divides_file (str): Filename of the incremental divides GeoPackage.
        precipitation_file (str): Filename of the raw precipitation Parquet file.
        ksat_file (str): Filename of the Ksat data Parquet file.
        outlet_discharge_file (str): Filename of the outlet discharge Parquet file.
        manning_params_file (str, optional): Filename of the Manning's parameters Parquet file.
                                             If None, this file will not be loaded. Defaults to None.

    Returns:
        tuple: A tuple containing all the loaded DataFrames and GeoDataFrames:
               (flowlines_gdf, divides_gdf, precip_df, ksat_df, 
                outlet_discharge_df, manning_params_df). 
               `manning_params_df` will be None if the file is not provided.
               
    Raises:
        FileNotFoundError: If any of the required files are not found.
    """
    print("Loading all input data...")
    
    def _load_file(filename, file_type, layer):
        full_path = data_path / filename
        if not full_path.exists():
            raise FileNotFoundError(f"Required data file not found: {full_path}")
        
        print(f"Reading {filename}...")
        if file_type == 'geopackage':
            return gpd.read_file(full_path, layer=layer)
        elif file_type == 'parquet':
            return pd.read_parquet(full_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    # Load all files
    flowlines_gdf = _load_file(flowlines_file, 'geopackage', 'flowlines')
    divides_gdf = _load_file(divides_file, 'geopackage', 'incremental_divides')
    precip_df = _load_file(precipitation_file, 'parquet')
    ksat_df = _load_file(ksat_file, 'parquet')
    outlet_discharge_df = _load_file(outlet_discharge_file, 'parquet')
    
    # Load optional Manning's file
    manning_params_df = None
    if manning_params_file:
        try:
            manning_params_df = _load_file(manning_params_file, 'parquet')
        except FileNotFoundError:
            print(f"Optional Manning's parameter file not found: {manning_params_file}. Will proceed without it.")
    
    return flowlines_gdf, divides_gdf, precip_df, ksat_df, outlet_discharge_df, manning_params_df