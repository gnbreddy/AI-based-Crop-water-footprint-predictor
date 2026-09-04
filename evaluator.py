import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

from config import (
    FINAL_MODEL_PATH,
    LOCAL_DATA_PATH,
    OUTPUT_DIR,
    EXTENDED_FEATURES,
    TARGET
)
from compiler import compile_datasets

def evaluate_locked_model_across_all_years(data_path=None, model_path=None):
    """
    Evaluates the fixed locked-in production model across every individual year
    (2000–2025), computing rigorous, authentic statistical metrics comparing
    actual ground-truth observations with algorithm predictions.
    
    Exports:
        - data/annual_prediction_accuracy_comparison.csv
        - outputs/annual_accuracy_comparison.png
        - individual annual residual tables
    """
    if model_path is None:
        model_path = FINAL_MODEL_PATH
    if data_path is None:
        master_csv = os.path.join(LOCAL_DATA_PATH, "master_engineered_dataset.csv")
        if os.path.exists(master_csv):
            print(f"[Evaluator] Loading compiled dataset from: {master_csv}")
            df = pd.read_csv(master_csv)
            df['datetime'] = pd.to_datetime(df['datetime'])
        else:
            print("[Evaluator] Compiling master dataset...")
            df = compile_datasets(LOCAL_DATA_PATH)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Locked production model not found at: {model_path}")

    print(f"[Evaluator] Loading locked production model from: {model_path}")
    model = joblib.load(model_path)

    # Match the base-plus-biophysical feature schema used by the production model.
    active_features = [f for f in EXTENDED_FEATURES if f in df.columns]
    years = sorted(df['year'].unique())
    print(f"[Evaluator] Evaluating across {len(years)} individual years ({years[0]} to {years[-1]})...\n")

    annual_metrics = []
    all_y_true = []
    all_y_pred = []

    for year in years:
        year_df = df[df['year'] == year].copy()
        if year_df.empty:
            continue

        y_true = year_df[TARGET].values
        y_pred = model.predict(year_df[active_features])

        # Exact mathematical metrics
        r2 = float(r2_score(y_true, y_pred))
        mse = float(mean_squared_error(y_true, y_pred))
        rmse = float(np.sqrt(mse))
        mae = float(mean_absolute_error(y_true, y_pred))
        
        # Pearson correlation
        corr = float(np.corrcoef(y_true, y_pred)[0, 1]) if len(y_true) > 1 else 1.0

        # Mean Absolute Percentage Error (avoiding zero division)
        nonzero_mask = y_true > 1e-4
        mape = float(np.mean(np.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])) * 100.0) if nonzero_mask.any() else 0.0

        actual_mean = float(np.mean(y_true))
        predicted_mean = float(np.mean(y_pred))
        bias = predicted_mean - actual_mean

        annual_metrics.append({
            'year': int(year),
            'sample_count': len(year_df),
            'r2_accuracy_pct': r2 * 100.0,
            'rmse_mm': rmse,
            'mae_mm': mae,
            'pearson_r': corr,
            'mape_pct': mape,
            'actual_mean_et_mm': actual_mean,
            'predicted_mean_et_mm': predicted_mean,
            'mean_bias_mm': bias
        })

        all_y_true.extend(y_true)
        all_y_pred.extend(y_pred)

        # Save individual year residual comparison CSV
        year_comparison_df = year_df[['datetime', 'month', 'day', 'hour']].copy() if 'datetime' in year_df.columns else pd.DataFrame()
        year_comparison_df['actual_' + TARGET] = y_true
        year_comparison_df['predicted_' + TARGET] = y_pred
        year_comparison_df['residual_error'] = y_true - y_pred
        year_comparison_df['abs_error'] = np.abs(y_true - y_pred)
        
        year_csv_path = os.path.join(LOCAL_DATA_PATH, f"prediction_comparison_{year}.csv")
        year_comparison_df.to_csv(year_csv_path, index=False)

    metrics_df = pd.DataFrame(annual_metrics)

    # Save summary CSV to data and outputs directories
    csv_save_path_data = os.path.join(LOCAL_DATA_PATH, "annual_prediction_accuracy_comparison.csv")
    csv_save_path_out = os.path.join(OUTPUT_DIR, "annual_prediction_accuracy_comparison.csv")
    metrics_df.to_csv(csv_save_path_data, index=False)
    metrics_df.to_csv(csv_save_path_out, index=False)

    print("=" * 80)
    print(f"{'Year':<6} | {'Samples':<8} | {'R² (%)':<8} | {'RMSE (mm)':<10} | {'MAE (mm)':<10} | {'Corr (r)':<9} | {'Bias (mm)'}")
    print("-" * 80)
    for _, row in metrics_df.iterrows():
        print(f"{int(row['year']):<6} | {int(row['sample_count']):<8} | {row['r2_accuracy_pct']:<8.2f} | {row['rmse_mm']:<10.4f} | {row['mae_mm']:<10.4f} | {row['pearson_r']:<9.4f} | {row['mean_bias_mm']:+.4f}")
    print("=" * 80)

    # Overall multi-decade statistics
    overall_r2 = float(r2_score(all_y_true, all_y_pred))
    overall_rmse = float(np.sqrt(mean_squared_error(all_y_true, all_y_pred)))
    overall_mae = float(mean_absolute_error(all_y_true, all_y_pred))
    print(f"\n[Summary] Overall Multi-Decade (2000–2025) Fixed-Model Accuracy:")
    print(f"  -> Global R²: {overall_r2*100:.2f}% | Global RMSE: {overall_rmse:.4f} mm | Global MAE: {overall_mae:.4f} mm\n")

    # Generate multi-panel comparison visualization
    plot_annual_comparison_visuals(metrics_df, np.array(all_y_true), np.array(all_y_pred))

    return metrics_df

def plot_annual_comparison_visuals(metrics_df, all_y_true, all_y_pred):
    """
    Generates a 3-panel authentic statistical comparison graph:
    1. Annual R² Accuracy (%) across 2000–2025.
    2. Annual RMSE & MAE (mm) error rates.
    3. Scatter Density Plot: Actual vs Predicted ET with 1:1 perfect parity line.
    """
    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.25)

    years = metrics_df['year'].values
    r2_vals = metrics_df['r2_accuracy_pct'].values
    rmse_vals = metrics_df['rmse_mm'].values
    mae_vals = metrics_df['mae_mm'].values

    # Panel 1: Year-by-Year R² Accuracy
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(years, r2_vals, marker='o', color='#1f77b4', linewidth=2, markersize=5, label='Yearly R² (%)')
    ax1.axhline(np.mean(r2_vals), color='#d62728', linestyle='--', label=f'Mean R² ({np.mean(r2_vals):.2f}%)')
    ax1.set_title("Annual Prediction Accuracy ($R^2$ Score %)", fontsize=12, fontweight='bold')
    ax1.set_ylabel("$R^2$ Accuracy (%)", fontsize=10)
    ax1.set_ylim(min(r2_vals) - 1.0, 100.0)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='lower left')

    # Panel 2: Year-by-Year Error Rates (RMSE & MAE)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(years, rmse_vals, marker='s', color='#ff7f0e', linewidth=2, markersize=5, label='RMSE (mm)')
    ax2.plot(years, mae_vals, marker='^', color='#2ca02c', linewidth=2, markersize=5, label='MAE (mm)')
    ax2.set_title("Annual Prediction Error (RMSE & MAE in mm)", fontsize=12, fontweight='bold')
    ax2.set_ylabel("Error (mm / 6-hour step)", fontsize=10)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='upper right')

    # Panel 3: Scatter Plot (Actual vs Predicted Evapotranspiration)
    ax3 = fig.add_subplot(gs[1, :])
    # Downsample points slightly for clean plotting if very large
    sample_indices = np.random.choice(len(all_y_true), size=min(5000, len(all_y_true)), replace=False)
    sub_true = all_y_true[sample_indices]
    sub_pred = all_y_pred[sample_indices]

    ax3.scatter(sub_true, sub_pred, alpha=0.25, color='#4b0082', s=12, edgecolors='none', label='6-Hourly Timestep Predictions')
    min_val = min(np.min(sub_true), np.min(sub_pred))
    max_val = max(np.max(sub_true), np.max(sub_pred))
    ax3.plot([min_val, max_val], [min_val, max_val], color='red', linestyle='--', linewidth=2, label='1:1 Perfect Parity Reference Line')
    ax3.set_title(f"Parity Scatter Comparison: Actual vs Predicted Evapotranspiration (N={len(all_y_true):,} records)", fontsize=12, fontweight='bold')
    ax3.set_xlabel("Actual Ground Truth ET ($mm$)", fontsize=10)
    ax3.set_ylabel("Algorithm Predicted ET ($mm$)", fontsize=10)
    ax3.grid(True, linestyle='--', alpha=0.5)
    ax3.legend(loc='upper left')

    save_path = os.path.join(OUTPUT_DIR, "annual_accuracy_comparison.png")
    plt.savefig(save_path, dpi=300)
    print(f"[Evaluator] Annual accuracy comparison chart saved to: {save_path}")
    plt.close()

if __name__ == "__main__":
    evaluate_locked_model_across_all_years()
