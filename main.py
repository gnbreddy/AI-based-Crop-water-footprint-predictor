import argparse
import os
import joblib
import pandas as pd
import numpy as np

from config import (
    MODEL_SAVE_PATH,
    OUTPUT_DIR,
    HEATMAP_TARGET_YEAR,
    LOCAL_DATA_PATH
)
from extractor import (
    authenticate_gee,
    extract_6hourly_data_for_year,
    download_6hourly_data_locally,
    check_task_status
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
from mock_data_generator import generate_mock_data

def run_pipeline(
    run_extract=False,
    run_download_local=False,
    run_mock=False,
    run_train=True,
    run_calibrate=True,
    run_visualize=True,
    deep_optimize=True,
    start_year=2000,
    end_year=2025,
    benchmark_twf=135.0
):
    print("=" * 75)
    print(" CROP WATER FOOTPRINT (CWF) MAXIMUM ACCURACY & EPOCH ENGINE")
    print("=" * 75)

    # 1A. Earth Engine Extraction to Google Drive (Batch Mode)
    if run_extract:
        print("\n[Stage 1A] Initializing Earth Engine Batch Tasks to Google Drive...")
        if authenticate_gee():
            for yr in range(start_year, end_year + 1):
                extract_6hourly_data_for_year(yr)
            check_task_status()
        else:
            print("[Stage 1A] GEE authentication skipped/failed.")

    # 1B. Direct Local Earth Engine Download (Direct Local CSV Mode)
    if run_download_local:
        print("\n[Stage 1B] Initializing Direct Earth Engine Download to Local ./data Folder...")
        if authenticate_gee():
            for yr in range(start_year, end_year + 1):
                download_6hourly_data_locally(yr)
        else:
            print("[Stage 1B] GEE authentication skipped/failed.")

    # 2. Mock Data Generation (Optional / Offline Mode)
    if run_mock:
        print(f"\n[Stage 2] Generating Multi-Year Synthetic 6-Hourly Datasets ({start_year} -> {end_year})...")
        generate_mock_data(start_year=start_year, end_year=end_year)

    # 3. Data Ingestion & Feature Compilation
    print("\n[Stage 3] Ingesting CSVs and Engineering Advanced Temporal Lag & Rolling Features...")
    df = compile_datasets(LOCAL_DATA_PATH)
    if df is None or df.empty:
        print("[Error] No data available to proceed. Run with --mock to generate test data or --download-local for GEE data.")
        return

    best_run = None
    # 4. Model Training & Expanding Window Cross-Validation for Maximum Accuracy
    if run_train:
        print("\n[Stage 4A] Training LightGBM Across Walk-Forward Epochs (2000–2025)...")
        best_run = train_and_evaluate(
            df,
            deep_search=deep_optimize,
            save_epoch_csvs=True,
            data_dir=LOCAL_DATA_PATH
        )

        print("\n[Stage 4B] Locking Final Production Weights on Complete Multi-Decade Dataset...")
        final_prod_run = train_final_production_model(df, data_dir=LOCAL_DATA_PATH)
        final_prod_run['full_history'] = best_run.get('full_history', [])
        best_run = final_prod_run

    # 5. Crop Water Footprint (CWF) Physical Calibration & Estimation
    cwf_results = None
    if run_calibrate:
        print("\n[Stage 5] Computing and Calibrating Crop Water Footprint Coefficients...")
        calibrator = CropWaterFootprintCalibrator()
        
        # Use target ET and precipitation from compiled dataset
        et_series = df['modis_et_mm'].values
        precip_series = df['precip'].values
        
        # Initial footprint computation
        cwf_initial = calibrator.compute_footprint(et_series, precip_series)
        print(f"  -> Initial Total Water Footprint: {cwf_initial['total_water_footprint_m3_ton']:.2f} m³/ton")
        print(f"     (Green: {cwf_initial['green_water_footprint_m3_ton']:.2f} m³/ton | Blue: {cwf_initial['blue_water_footprint_m3_ton']:.2f} m³/ton)")

        # Empirical coefficient calibration against target benchmark
        calib_output = calibrator.calibrate_coefficients(
            et_series=et_series,
            precip_series=precip_series,
            target_twf=benchmark_twf,
            target_gwf_ratio=0.70
        )
        cwf_results = calib_output['calibrated_footprint']

        # Save calibrated water footprint timeseries to data folder
        cwf_ts_df = df[['datetime', 'year', 'month', 'day', 'hour']].copy() if 'datetime' in df.columns else pd.DataFrame()
        cwf_ts_df['et_actual_mm'] = et_series
        cwf_ts_df['et_crop_adjusted_mm'] = cwf_results['et_c_series']
        cwf_ts_df['effective_precip_mm'] = cwf_results['p_eff_series']
        cwf_ts_df['et_green_mm'] = cwf_results['et_green_series']
        cwf_ts_df['et_blue_mm'] = cwf_results['et_blue_series']
        
        cwf_ts_path = os.path.join(LOCAL_DATA_PATH, "calibrated_cwf_timeseries.csv")
        cwf_ts_df.to_csv(cwf_ts_path, index=False)
        print(f"[Stage 5] Saved calibrated CWF timeseries dataset to: {cwf_ts_path}")

    # 6. Visualizations and Spatial Map Generation
    if run_visualize:
        print("\n[Stage 6] Generating Visual Analytics, Learning Curves, and Spatial Map...")
        if best_run:
            plot_feature_importance(best_run)
            if 'full_history' in best_run:
                plot_learning_curve(best_run['full_history'])
        
        if cwf_results:
            plot_water_footprint_breakdown(cwf_results)
            
        target_map_year = best_run['predicted_year'] if best_run else HEATMAP_TARGET_YEAR
        generate_footprint_map(target_map_year)

    print("\n" + "=" * 75)
    print(" PIPELINE EXECUTION COMPLETE: ALL EPOCH CSVS & ARTIFACTS PERSISTED")
    print(f" Data Directory:   {LOCAL_DATA_PATH}")
    print(f" Output Directory: {OUTPUT_DIR}")
    print("=" * 75)

def main():
    parser = argparse.ArgumentParser(description="Crop Water Footprint (CWF) Maximum Accuracy & Epoch Pipeline")
    parser.add_argument("--mock", action="store_true", help="Generate synthetic 6-hourly datasets for testing")
    parser.add_argument("--extract", action="store_true", help="Dispatch Earth Engine data extraction batch jobs to Google Drive")
    parser.add_argument("--download-local", action="store_true", help="Download GEE data directly to local ./data CSV files")
    parser.add_argument("--train", action="store_true", help="Run LightGBM model training across walk-forward epochs")
    parser.add_argument("--deep-optimize", action="store_true", default=True, help="Run deep search for maximum accuracy")
    parser.add_argument("--calibrate", action="store_true", help="Run CWF physical coefficient calibration")
    parser.add_argument("--visualize", action="store_true", help="Generate plots and interactive Folium maps")
    parser.add_argument("--all", action="store_true", help="Run full end-to-end pipeline (mock/compile/train/calibrate/visualize)")
    parser.add_argument("--start-year", type=int, default=2000, help="Starting year for data processing (default 2000)")
    parser.add_argument("--end-year", type=int, default=2025, help="Ending year for data processing (default 2025)")
    parser.add_argument("--benchmark-twf", type=float, default=135.0, help="Target total water footprint benchmark (m3/ton)")

    args = parser.parse_args()

    # Default behavior if no specific flags passed
    if args.all or not (args.mock or args.extract or args.download_local or args.train or args.calibrate or args.visualize):
        run_pipeline(
            run_extract=args.extract,
            run_download_local=args.download_local,
            run_mock=args.mock or not os.path.exists(LOCAL_DATA_PATH) or len([f for f in os.listdir(LOCAL_DATA_PATH) if f.endswith('.csv')]) == 0,
            run_train=True,
            run_calibrate=True,
            run_visualize=True,
            deep_optimize=True,
            start_year=args.start_year,
            end_year=args.end_year,
            benchmark_twf=args.benchmark_twf
        )
    else:
        run_pipeline(
            run_extract=args.extract,
            run_download_local=args.download_local,
            run_mock=args.mock,
            run_train=args.train,
            run_calibrate=args.calibrate,
            run_visualize=args.visualize,
            deep_optimize=args.deep_optimize,
            start_year=args.start_year,
            end_year=args.end_year,
            benchmark_twf=args.benchmark_twf
        )

if __name__ == "__main__":
    main()
