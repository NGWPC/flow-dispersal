import pandas as pd
import geopandas as gpd
from pathlib import Path
import warnings
from src.dataloader import load_all_data
from src.precipitaiton import process_precipitation_data  
from src.landcover import calculate_average_runoff_coefficient
from src.disaggregate import calculate_disaggregated_discharge
warnings.filterwarnings("ignore", category=UserWarning)

def main():    
    print("Starting the watershed discharge disaggregation workflow.")
    # Define the location of your data and output files
    DATA_PATH = Path("data")
    DATA_PATH.mkdir(exist_ok=True)
    # Define the filenames for all your input data
    FLOWLINES_FILE = "disaggreagtion_test.gpkg"
    DIVIDES_FILE = "disaggreagtion_test.gpkg"
    PRECIPITATION_FILE = "all_geometries_precipitation.parquet"
    KSAT_FILE = "ksat_table_inc_divides.parquet"
    OUTLET_DISCHARGE_FILE = "daily_discharge.parquet"
    MANNING_PARAMS_FILE = "manning_parameters.parquet" # This one is optional

    try:
        flowlines, divides, raw_precip, ksat_table, outlet_q, manning_params = load_all_data(
            data_path=DATA_PATH,
            flowlines_file=FLOWLINES_FILE,
            divides_file=DIVIDES_FILE,
            precipitation_file=PRECIPITATION_FILE,
            ksat_file=KSAT_FILE,
            outlet_discharge_file=OUTLET_DISCHARGE_FILE,
            manning_params_file=MANNING_PARAMS_FILE
        )
        
        aggregated_rain_df = process_precipitation_data(
            rain_df=raw_precip,
            processing_mode='aggregate'
        )
  
        nlcd_tif_path = DATA_PATH / "nlcd_clipped.tif"
        if not nlcd_tif_path.exists():
            raise FileNotFoundError(f"Runoff calculation requires NLCD raster file not found at: {nlcd_tif_path}")

        runoff_gdf = calculate_average_runoff_coefficient(
            tif_path=nlcd_tif_path,
            divides_df=divides,
            level='level1'
        )

        # Disaggregate Discharge  
        print("\n[3/4] Calculating disaggregated discharge...")
        final_disaggregated_gdf, flowlines_with_calcs_gdf, final_label = calculate_disaggregated_discharge(
            flowlines_gdf=flowlines,
            runoff_gdf=runoff_gdf,
            precipitation_df=aggregated_rain_df,
            ksat_df=ksat_table,
            outlet_discharge_df=outlet_q,
            manning_params_df=manning_params,
            use_level1_runoff=True,
            use_travel_time_dilation=True
        )
        print(f"Disaggregation complete. Generated label: {final_label}")

        # Save Outputs to CSV Files  
        print(f"\nSaving results to CSV files in '{DATA_PATH}' directory...")
        
        disaggregated_output_path = DATA_PATH / f"disaggregated_discharge_{final_label}.csv"
        intermediate_calcs_output_path = DATA_PATH / f"flowline_calculations_{final_label}.csv"

        final_disaggregated_gdf.drop(columns='geometry').to_csv(disaggregated_output_path, index=False)
        flowlines_with_calcs_gdf.drop(columns='geometry').to_csv(intermediate_calcs_output_path, index=False)
        
        print(f"Saved final disaggregated discharge to: {disaggregated_output_path}")
        print(f"Saved intermediate calculations to: {intermediate_calcs_output_path}")

    except FileNotFoundError as e:
        print(f"\nERROR: A required data file was not found.")
        print(e)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        print("\n Workflow Complete.")


if __name__ == "__main__":
    main()