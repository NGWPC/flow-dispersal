# precipitaiton.py
import pandas as pd
from typing import Literal

def process_precipitation_data(
    rain_df: pd.DataFrame,
    processing_mode: Literal['daily', 'aggregate'] = 'daily'
) -> pd.DataFrame:
    """
    Loads and processes precipitation data from a Parquet file.

    This function can return the data in one of two modes:
    1. 'daily': (Default) Cleans and formats the data into a daily time series.
       The 'time' column is normalized to midnight UTC.
    2. 'aggregate': Aggregates the data by 'flowline_id', summing the
       precipitation values over the entire period to get a single total
       value for each 'flowline_id'.

    Args:
        rain_df (pd.DataFrame):
            The precipitation dataframe that is expected to
            contain 'time', 'flowline_id', and precipitation columns.
        processing_mode (Literal['daily', 'aggregate'], optional):
            The mode of processing to perform.
            - 'daily': Returns a cleaned daily time series DataFrame.
            - 'aggregate': Returns a DataFrame with total precipitation
              summed for each 'flowline_id'.
            Defaults to 'daily'.

    Returns:
        pd.DataFrame:
            A DataFrame containing the processed precipitation data, either as
            a daily time series or as an aggregated summary.

    Raises:
        ValueError: If the 'processing_mode' argument is not 'daily' or 'aggregate'.
    """
    rain_df['time'] = pd.to_datetime(rain_df['time'])
    rain_df['time'] = rain_df['time'].dt.tz_localize('UTC', ambiguous='infer')
    rain_df['time'] = rain_df['time'].dt.normalize()

    if processing_mode == 'daily':
        return rain_df
    
    elif processing_mode == 'aggregate':
        rain_df.pop('time')
        
        rain_aggregated_df = rain_df.groupby('flowline_id').sum()
        rain_aggregated_df.reset_index(inplace=True)
        
        return rain_aggregated_df
        
    else:
        raise ValueError("Invalid processing_mode. Choose either 'daily' or 'aggregate'.")