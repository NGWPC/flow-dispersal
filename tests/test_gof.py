# test_gof.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import hydrostats.metrics as he

def analyze_discharge_goodness_of_fit_compact(df: pd.DataFrame, measured_col: str, predicted_col: str, 
                                              site_id_col: str, time_col: str, label: str) -> pd.DataFrame:
    """
    Computes a set of goodness-of-fit metrics and 
    compare measured and predicted discharge across different sites.

    Args:
        df (pd.DataFrame): DataFrame containing the data. It must have a datetime index.
        measured_col (str): The name of the column with measured discharge data.
        predicted_col (str): The name of the column with predicted discharge data.
        site_id_col (str): The name of the column with the site identifiers.
        time_col (str): The name of the column with the timestamp data.
    """
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'serif'

    site_ids = df[site_id_col].unique()
    all_metrics = []

    # Loop through each site
    for site_id in site_ids:
        print(f"Analyzing Site: {site_id}")
        site_df = df[df[site_id_col] == site_id].copy()
        site_df[time_col] = pd.to_datetime(site_df[time_col])
        site_df = site_df.set_index(time_col)

        # Goodness-of-Fit Metrics Calculation
        # For calculation, drop any rows where either measured or predicted is NaN
        eval_df = site_df[[measured_col, predicted_col]].dropna()
        measured = eval_df[measured_col]
        predicted = eval_df[predicted_col]

        metrics = {
            'Site ID': site_id,
            'NSE': he.nse(predicted, measured),
            'RMSE': he.rmse(predicted, measured),
            'MAE': he.mae(predicted, measured),
            'R-Squared': he.r_squared(predicted, measured),
            'Index of Agreement (d)': he.d(predicted, measured)
        }
        all_metrics.append(metrics)
        
        # Print the metrics for the current site
        print("\nGoodness-of-Fit Metrics:")
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"{key}: {value:.3f}")


        fig, axs = plt.subplots(2, 2, figsize=(20, 12))
        fig.suptitle(f'Discharge Goodness-of-Fit Analysis for Site: {site_id}', fontsize=24, y=0.95)

        # Plot 1: Hydrograph Comparison
        axs[0, 0].plot(site_df.index, site_df[measured_col], label='Measured', color='black', alpha=0.8)
        axs[0, 0].plot(site_df.index, site_df[predicted_col], label='Calculated', color='crimson', linestyle='--')
        axs[0, 0].set_title('Hydrograph Comparison', fontsize=16)
        axs[0, 0].set_xlabel('Date', fontsize=12)
        axs[0, 0].set_ylabel('Discharge', fontsize=12)
        axs[0, 0].legend()
        axs[0, 0].tick_params(axis='x', rotation=45)

        # Plot 2: Scatter Plot of Calculated vs. Measured
        sns.regplot(x=measured, y=predicted, ax=axs[0, 1], color='darkblue',
                    line_kws={'color': 'red', 'linestyle': '--', 'label': 'Regression Line'},
                    scatter_kws={'alpha': 0.6, 'edgecolor': 'w'})
        axs[0, 1].plot([measured.min(), measured.max()], [measured.min(), measured.max()], 'k--', label='1:1 Line')
        axs[0, 1].set_title('Calculated vs. Measured Discharge', fontsize=16)
        axs[0, 1].set_xlabel('Measured Discharge', fontsize=12)
        axs[0, 1].set_ylabel('Calculated Discharge', fontsize=12)
        axs[0, 1].legend()
        metrics_text = (
            f"NSE: {metrics['NSE']:.3f}\n"
            f"MAE: {metrics['MAE']:.3f}\n"
            f"RMSE: {metrics['RMSE']:.3f}\n"
            f"R²: {metrics['R-Squared']:.3f}\n"
            f"Index of Agreement: {metrics['Index of Agreement (d)']:.1f}%"
        )
        bbox_props = dict(boxstyle="round,pad=0.5", fc="ivory", ec="black", lw=1, alpha=0.8)
        axs[0, 1].text(0.05, 0.95, metrics_text, transform=axs[0, 1].transAxes,
                       fontsize=12, verticalalignment='top', bbox=bbox_props)        
        axs[0, 1].legend()
        residuals = measured - predicted

        # Plot 3: Distribution of Residuals
        sns.histplot(residuals, kde=True, ax=axs[1, 0], color='teal')
        axs[1, 0].axvline(0, color='red', linestyle='--')
        axs[1, 0].set_title('Distribution of Residuals', fontsize=16)
        axs[1, 0].set_xlabel('Residual Value', fontsize=12)
        axs[1, 0].set_ylabel('Frequency', fontsize=12)

        # Plot 4: Monthly Average Comparison
        monthly_avg = site_df[[measured_col, predicted_col]].resample('M').mean()
        monthly_avg.plot(kind='bar', ax=axs[1, 1], color=['black', 'crimson'])
        axs[1, 1].set_title('Monthly Average Discharge Comparison', fontsize=16)
        axs[1, 1].set_xlabel('Month', fontsize=12)
        axs[1, 1].set_ylabel('Average Discharge', fontsize=12)
        axs[1, 1].set_xticklabels([d.strftime('%Y-%m') for d in monthly_avg.index], rotation=90)
        axs[1, 1].legend()

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig("data/"+label+"_"+site_id+".png", dpi=300)
        plt.show()

    metrics_df = pd.DataFrame(all_metrics)
    print("\nSummary of Goodness-of-Fit Metrics Across All Sites:")
    print(metrics_df.to_string())
    return metrics_df