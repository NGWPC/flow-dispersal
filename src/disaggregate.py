# disaggregate.py

import pandas as pd
import geopandas as gpd
import numpy as np
import warnings
from typing import Tuple

def _get_total_travel_time(flowline_id: int, time_map: dict, to_map: dict, outlet_id: int=-1) -> float:
    """
    Sum travel time down to the outlet.
    
    Args:
        flowline_id (int): The starting flowline ID.
        time_map (dict): A dictionary mapping flowline_id to its segment travel time.
        to_map (dict): A dictionary mapping flowline_id to its downstream flowline_id.

    Returns:
        float: The total travel time from the flowline to the basin outlet in seconds.
    """
    if flowline_id == outlet_id:  # Reached the outlet (not needed for now)
        return 0
    current_segment_time = time_map.get(flowline_id, 0)
    downstream_id = to_map.get(flowline_id, -1)
    
    return current_segment_time + _get_total_travel_time(downstream_id, time_map, to_map)


def calculate_disaggregated_discharge(
    flowlines_gdf: gpd.GeoDataFrame,
    runoff_gdf: gpd.GeoDataFrame,
    precipitation_df: pd.DataFrame,
    ksat_df: pd.DataFrame,
    outlet_discharge_df: pd.DataFrame,
    manning_params_df: pd.DataFrame = None,
    alpha: float = 1.0,
    beta: float = 1.0,
    gamma: float = 1.0,
    omega: float = 1.0,
    use_level1_runoff: bool = True,
    use_cumulative_area: bool = True,
    use_travel_time_dilation: bool = True,
    scale_inputs: bool = True

) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, str]:
    """
    Calculates and disaggregates watershed discharge across all flowlines based on
    a weighted influence score and accounts for hydrologic travel time.
    Method inherently preserves mass.
    Note: All inputs should be in SI (e.g., discharge unit m³/s)

    Args:
        flowlines_gdf (gpd.GeoDataFrame): GeoDataFrame of flowlines with 'flowline_id' and 'to_id'.
        runoff_gdf (gpd.GeoDataFrame): GDF with Level 1 or 2 runoff coefficients and 'flowline_id'.
        precipitation_df (pd.DataFrame): DataFrame with precipitation data ('prcp_sum') and 'flowline_id'.
        ksat_df (pd.DataFrame): DataFrame with Ksat values ('ksat') and 'flowline_id'.
        outlet_discharge_df (pd.DataFrame): Time series of observed discharge at the outlet with 'time' and 'discharge'.
        manning_params_df (pd.DataFrame, optional): DataFrame with Manning's parameters for travel time
            (requires 'flowline_id', 'slope', 'mannings_n', 'channel_area', 'wetted_perimeter'). 
            If None, hardcoded placeholders are used. Defaults to None.
        alpha (float): Exponent for the area term.
        beta (float): Exponent for the runoff coefficient term.
        gamma (float): Exponent for the precipitation term.
        omega (float): Exponent for the hydraulic conductivity (Ksat) term.
        use_level1_runoff (bool): If True, use Level 1 runoff data. Otherwise, use Level 2.
        use_cumulative_area (bool): If True, use 'drainage_area'. Otherwise, use 'area_incr'.
        use_travel_time_dilation (bool): If True, calculate and apply travel time lag.
        scale_inputs (bool): If True, scales ksat, precipitation, and area to a 1-10 range before scoring.

    Returns:
        Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, str]:
        - final_disaggregated_gdf: A GeoDataFrame with the time-disaggregated discharge for each flowline.
        - flowlines_with_calcs_gdf: The input flowlines GDF with all intermediate calculations
          (influence_score, runoff_weight, travel_time_days).
        - final_label: A string label describing the parameters used (e.g., 'A_RC_L1_P_K_TT').
    """
    flowlines_working_copy = flowlines_gdf.copy()
    flowlines_working_copy['flowline_id'] = flowlines_working_copy['flowline_id'].astype('Int64')
    flowlines_working_copy['to_id'] = flowlines_working_copy['to_id'].astype('Int64')

    # Select appropriate runoff data and area column
    runoff_df = runoff_gdf.copy() 
    area_label = 'drainage_area' if use_cumulative_area else 'area_incr'
    merged_df = runoff_df.merge(ksat_df[['flowline_id', 'ksat']], on='flowline_id', how='left')
    merged_df = merged_df.merge(precipitation_df, on='flowline_id', how='left')
    merged_df = merged_df.merge(flowlines_working_copy[['flowline_id', area_label]], on='flowline_id', how='left')

    if scale_inputs:
        cols_to_scale = ['ksat', 'prcp_sum', area_label]
        for col in cols_to_scale:
            min_val = merged_df[col].min()
            max_val = merged_df[col].max()
            merged_df[col] = 1 + (merged_df[col] - min_val) * 9 / (max_val - min_val + 1e-9)

    # Calculate influence score
    merged_df['influence_score'] = (
        (merged_df[area_label]**alpha) * 
        (merged_df['avg_runoff_coeff']**beta) * 
        (merged_df['prcp_sum']**gamma) / 
        (merged_df['ksat']**omega + 1e-9) 
    )
    
    # Normalize to get runoff weight
    max_influence_score = merged_df['influence_score'].max()
    merged_df['runoff_weight'] = merged_df['influence_score'] / (max_influence_score + 1e-9)
    weights_df = merged_df[['flowline_id', 'runoff_weight', 'influence_score']]
    flowlines_with_calcs_gdf = flowlines_working_copy.merge(weights_df, on='flowline_id', how='left')

    # Calculate Travel Time  
    if use_travel_time_dilation:
        if manning_params_df is None:
            warnings.warn("`manning_params_df` not provided. Using hardcoded placeholder values for travel time calculation.")
            flowlines_with_calcs_gdf['slope'] = 0.01
            flowlines_with_calcs_gdf['mannings_n'] = 0.02
            flowlines_with_calcs_gdf['channel_area'] = 10
            flowlines_with_calcs_gdf['wetted_perimeter'] = 9
        else:
            flowlines_with_calcs_gdf = flowlines_with_calcs_gdf.merge(manning_params_df, on='flowline_id', how='left')

        flowlines_with_calcs_gdf['length_m'] = flowlines_with_calcs_gdf.geometry.length
        flowlines_with_calcs_gdf['hydraulic_radius'] = flowlines_with_calcs_gdf['channel_area'] / flowlines_with_calcs_gdf['wetted_perimeter']
        flowlines_with_calcs_gdf['velocity_mps'] = (
            (1 / flowlines_with_calcs_gdf['mannings_n']) *
            (flowlines_with_calcs_gdf['hydraulic_radius'] ** (2/3)) *
            (flowlines_with_calcs_gdf['slope'] ** 0.5)
        )
        flowlines_with_calcs_gdf['segment_travel_time_s'] = flowlines_with_calcs_gdf['length_m'] / flowlines_with_calcs_gdf['velocity_mps']
        
        time_map = flowlines_with_calcs_gdf.set_index('flowline_id')['segment_travel_time_s'].to_dict()
        to_map = flowlines_with_calcs_gdf.set_index('flowline_id')['to_id'].to_dict()

        flowlines_with_calcs_gdf['total_travel_time_s'] = flowlines_with_calcs_gdf['flowline_id'].apply(
            lambda fid: _get_total_travel_time(fid, time_map, to_map)
        )
        flowlines_with_calcs_gdf['travel_time_days'] = (flowlines_with_calcs_gdf['total_travel_time_s'] / (3600 * 24)).round().astype(int)
    else:
        flowlines_with_calcs_gdf['travel_time_days'] = 0

    # Disaggregate Observed Discharge  
    disaggregated_results = []
    sorted_outlet_q = outlet_discharge_df.sort_values('time').reset_index(drop=True)

    for _, flowline_data in flowlines_with_calcs_gdf.iterrows():
        weight = flowline_data['runoff_weight']
        lag_days = flowline_data['travel_time_days']
        fid = flowline_data['flowline_id']
        
        if pd.isna(weight) or weight == 0:
            continue
            
        flowline_disaggregated = sorted_outlet_q[['time']].copy()
        flowline_disaggregated['flowline_id'] = fid
        
        # Shift outlet discharge *backwards* by lag_days  
        shifted_outlet_q = sorted_outlet_q['discharge'].shift(-lag_days)
        flowline_disaggregated['disaggregated_discharge'] = shifted_outlet_q * weight
        
        disaggregated_results.append(flowline_disaggregated)

    final_disaggregated_df = pd.concat(disaggregated_results).fillna(0)
    final_disaggregated_gdf = gpd.GeoDataFrame(
        final_disaggregated_df.merge(flowlines_with_calcs_gdf[['flowline_id', 'geometry']], on='flowline_id'),
        geometry='geometry', crs=flowlines_gdf.crs
    )

    # Label 
    a_lab = 'A' if alpha != 0 else ''
    b_lab = f'RC_L{1 if use_level1_runoff else 2}' if beta != 0 else ''
    g_lab = 'P' if gamma != 0 else ''
    o_lab = 'K' if omega != 0 else ''
    t_lab = 'TT' if use_travel_time_dilation else ''
    final_label = '_'.join(filter(None, [a_lab, b_lab, g_lab, o_lab, t_lab]))

    return final_disaggregated_gdf, flowlines_with_calcs_gdf, final_label