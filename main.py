import argparse
import os
import joblib
import pandas as pd
import numpy as np

from config import (
    MODEL_SAVE_PATH,
    OUTPUT_DIR,
    HEATMAP_TARGET_YEAR,
    LOCAL_DATA_PATH,
    REGIONS
)
from extractor import (
    authenticate_gee,
    export_epoch_to_drive,
    extract_epoch_directly_to_local,
    check_task_statuses
)
from compiler import compile_datasets
from trainer import train_and_evaluate, train_final_production_model
from calibrator import CropWaterFootprintCalibrator
from visualizer import (
    plot_feature_importance,
    plot_water_footprint_breakdown,
    plot_learning_curve,
    generate_footprint_map
)

def run_pipeline(
    run_extract_drive=False,
    run_extract_direct=False,
    run_train=True,
    run_calibrate=True,
    run_visualize=True,
    deep_optimize=True,
    start_year=2000,
    end_year=2025,
    benchmark_twf=135.0,
    project_id=None
):
    print("=" * 80)
    print(" AQUACROP AI: AUTHENTIC GEE INGESTION & PRODUCTION TRAINING PIPELINE")
    print("=" * 80)

    # 1A. Earth Engine Extraction to Google Drive (Cloud Batch Mode)
    if run_extract_drive:
        print("\n[Stage 1A] Dispatching Earth Engine Cloud Batch Export Tasks to Google Drive...")
        if authenticate_gee(project_id):
            for yr in range(start_year, end_year + 1):
                export_epoch_to_drive(yr)
            check_task_statuses()
        else:
            print("[Stage 1A] GEE authentication skipped/failed.")
            return

    # 1B. Direct Local Earth Engine Download (Direct Local Mode)
    if run_extract_direct:
        print(f"\n[Stage 1B] Streaming Authentic GEE Data Directly into {LOCAL_DATA_PATH}...")
        if authenticate_gee(project_id):
            for yr in range(start_year, end_year + 1):
                extract_epoch_directly_to_local(yr)
        else:
            print("[Stage 1B] GEE authentication skipped/failed.")
            return

    # 2. Data Ingestion & Feature Compilation
    print("\n[Stage 2] Ingesting GEE Epoch Datasets & Engineering Non-Bleeding Lag Features...")
    df = compile_datasets(LOCAL_DATA_PATH)
    if df is None or df.empty:
        print("[Notice] No compiled datasets found in data/.")
        print("To extract authentic data from Google Earth Engine, run:")
        print("  python extractor.py --mode direct --start-year 2000 --end-year 2025")
        print("or dispatch Google Drive batch tasks with:")
        print("  python extractor.py --mode drive --start-year 2000 --end-year 2025")
        return

    print(f"[Stage 2] Master Dataset Ready: {len(df):,} records.")

    best_run = None
    # 3. Model Training & Expanding Window Cross-Validation
    if run_train:
        print("\n[Stage 3A] Training LightGBM Across Walk-Forward Annual Epochs (2000–2025)...")
        best_run = train_and_evaluate(
            df,
            deep_search=deep_optimize,
            save_epoch_csvs=True,
            data_dir=LOCAL_DATA_PATH
        )

        print("\n[Stage 3B] Locking Final Production Weights on Master Multi-Decade Pool...")
        final_prod_run = train_final_production_model(df, data_dir=LOCAL_DATA_PATH)
        final_prod_run['full_history'] = best_run.get('full_history', [])
        best_run = final_prod_run

    # 4. Crop Water Footprint (CWF) Physical Calibration & Estimation
    cwf_results = None
    if run_calibrate:
        print("\n[Stage 4] Computing & Calibrating Crop Water Footprint Coefficients...")
        calibrator = CropWaterFootprintCalibrator()
        
        et_series = df['modis_et_mm'].values
        precip_series = df['precip'].values
        
        cwf_initial = calibrator.compute_footprint(et_series, precip_series)
        print(f"  -> Initial Total Water Footprint: {cwf_initial['total_water_footprint_m3_ton']:.2f} m³/ton")
        print(f"     (Green: {cwf_initial['green_water_footprint_m3_ton']:.2f} m³/ton | Blue: {cwf_initial['blue_water_footprint_m3_ton']:.2f} m³/ton)")

        calib_output = calibrator.calibrate_coefficients(
            et_series=et_series,
            precip_series=precip_series,
            target_twf=benchmark_twf,
            target_gwf_ratio=0.70
        )
        cwf_results = calib_output['calibrated_footprint']

        cwf_ts_df = df[['datetime', 'year', 'month', 'day', 'hour']].copy() if 'datetime' in df.columns else pd.DataFrame()
        cwf_ts_df['et_actual_mm'] = et_series
        cwf_ts_df['et_crop_adjusted_mm'] = cwf_results['et_c_series']
        cwf_ts_df['effective_precip_mm'] = cwf_results['p_eff_series']
        cwf_ts_df['et_green_mm'] = cwf_results['et_green_series']
        cwf_ts_df['et_blue_mm'] = cwf_results['et_blue_series']
        
        cwf_ts_path = os.path.join(LOCAL_DATA_PATH, "calibrated_cwf_timeseries.csv")
        cwf_ts_df.to_csv(cwf_ts_path, index=False)
        print(f"[Stage 4] Saved calibrated CWF timeseries dataset to: {cwf_ts_path}")

    # 5. Visualizations & Spatial Map Generation
    if run_visualize:
        print("\n[Stage 5] Generating Visual Analytics & Model Diagnostics...")
        if best_run:
            plot_feature_importance(best_run)
            if 'full_history' in best_run:
                plot_learning_curve(best_run['full_history'])
        
        if cwf_results:
            plot_water_footprint_breakdown(cwf_results)
            
        target_map_year = best_run['predicted_year'] if best_run else HEATMAP_TARGET_YEAR
        generate_footprint_map(target_map_year)

    print("\n" + "=" * 80)
    print(" PIPELINE EXECUTION COMPLETE")
    print(f" Data Directory:   {LOCAL_DATA_PATH}")
    print(f" Output Directory: {OUTPUT_DIR}")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="AquaCrop AI End-to-End Execution Pipeline")
    parser.add_argument("--extract-drive", action="store_true", help="Dispatch GEE batch extraction tasks to Google Drive (folder: GEE_CWF_Data)")
    parser.add_argument("--extract-direct", action="store_true", help="Directly stream authentic GEE data into local data/ directory")
    parser.add_argument("--train", action="store_true", help="Run LightGBM model training across walk-forward epochs")
    parser.add_argument("--deep-optimize", action="store_true", default=True, help="Run hyperparameter optimization")
    parser.add_argument("--calibrate", action="store_true", help="Run CWF physical coefficient calibration")
    parser.add_argument("--visualize", action="store_true", help="Generate analytics charts and maps")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--start-year", type=int, default=2000, help="Starting year for epochs (default: 2000)")
    parser.add_argument("--end-year", type=int, default=2025, help="Ending year for epochs (default: 2025)")
    parser.add_argument("--project", type=str, default=None, help="Google Cloud Project ID for Earth Engine")
    parser.add_argument("--benchmark-twf", type=float, default=135.0, help="Target total water footprint benchmark (m3/ton)")

    args = parser.parse_args()

    run_pipeline(
        run_extract_drive=args.extract_drive,
        run_extract_direct=args.extract_direct,
        run_train=args.train or args.all,
        run_calibrate=args.calibrate or args.all,
        run_visualize=args.visualize or args.all,
        deep_optimize=args.deep_optimize,
        start_year=args.start_year,
        end_year=args.end_year,
        benchmark_twf=args.benchmark_twf,
        project_id=args.project
    )

if __name__ == "__main__":
    main()
