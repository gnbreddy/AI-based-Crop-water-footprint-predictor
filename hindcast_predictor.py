import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from config import (
    FINAL_MODEL_PATH,
    LOCAL_DATA_PATH,
    OUTPUT_DIR,
    FEATURES,
    BASE_FEATURES,
    DEFAULT_CWF_PARAMS
)
from calibrator import CropWaterFootprintCalibrator

def generate_1990s_meteorological_inputs(start_year=1990, end_year=1999, data_dir=LOCAL_DATA_PATH):
    """
    Generates unlabelled meteorological input driver sequences for 1990–1999
    (without any target MODIS ET labels, which did not exist prior to 2000).
    """
    os.makedirs(data_dir, exist_ok=True)
    np.random.seed(1990)

    dfs = []
    print(f"[Hindcast] Synthesizing pure meteorological driver features ({start_year} -> {end_year}) without target ET...")

    for year in range(start_year, end_year + 1):
        date_rng = pd.date_range(
            start=f'{year}-01-01 00:00:00',
            end=f'{year}-12-31 18:00:00',
            freq='6h'
        )
        n_samples = len(date_rng)

        df = pd.DataFrame({'datetime': date_rng})
        df['year'] = df['datetime'].dt.year
        df['month'] = df['datetime'].dt.month
        df['day'] = df['datetime'].dt.day
        df['hour'] = df['datetime'].dt.hour
        df['system:time_start'] = df['datetime'].astype('int64') // 10**6

        day_of_year = df['datetime'].dt.dayofyear.values
        hour_of_day = df['hour'].values

        # Historical 1990s climatic variations
        temp_annual = 25.8 + 8.2 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        temp_diurnal = 5.0 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        df['temp_c'] = temp_annual + temp_diurnal + np.random.normal(0, 1.6, n_samples)

        df['wind_speed'] = np.clip(3.6 + 1.4 * np.sin(2 * np.pi * day_of_year / 365) + np.random.exponential(1.5, n_samples), 0.5, 20.0)
        df['pressure_kpa'] = 98.5 + 1.0 * np.cos(2 * np.pi * day_of_year / 365) + np.random.normal(0, 0.3, n_samples)

        solar_base = np.maximum(0, np.sin(np.pi * (hour_of_day - 6) / 12))
        df['solar_rad'] = solar_base * (18.0 + 5.0 * np.cos(2 * np.pi * (day_of_year - 172) / 365)) + np.random.uniform(0, 1.0, n_samples)

        is_monsoon = (day_of_year >= 150) & (day_of_year <= 270)
        rain_prob = np.where(is_monsoon, 0.36, 0.05)
        rain_event = np.random.binomial(1, rain_prob, n_samples)
        df['precip'] = rain_event * np.random.gamma(shape=2.0, scale=4.2, size=n_samples)

        df['soil_moisture'] = np.clip(0.15 + 0.15 * np.sin(2 * np.pi * (day_of_year - 140) / 365) + (df['precip'] * 0.01) + np.random.normal(0, 0.02, n_samples), 0.08, 0.48)
        df['ndvi'] = np.clip(0.35 + 0.35 * np.sin(2 * np.pi * (day_of_year - 180) / 365) + np.random.normal(0, 0.03, n_samples), 0.1, 0.9)

        # Notice: NO TARGET ET IS CREATED OR LOOKED AT

        # Save individual year input files
        year_file = os.path.join(data_dir, f"inputs_1990s_{year}.csv")
        df.to_csv(year_file, index=False)
        dfs.append(df)

    master_1990s = pd.concat(dfs, ignore_index=True)
    return master_1990s

def engineer_features_for_hindcast(df):
    """Applies the exact 22-feature engineering transformations."""
    df = df.sort_values(by='datetime').reset_index(drop=True)

    # Multi-step lags
    df['temp_c_lag1'] = df['temp_c'].shift(1)
    df['precip_lag1'] = df['precip'].shift(1)
    df['ndvi_lag1'] = df['ndvi'].shift(1)
    df['soil_moisture_lag1'] = df['soil_moisture'].shift(1)
    df['temp_c_lag4'] = df['temp_c'].shift(4)
    df['soil_moisture_lag4'] = df['soil_moisture'].shift(4)

    # Rolling window statistics
    df['temp_c_roll24h'] = df['temp_c'].rolling(window=4, min_periods=1).mean()
    df['solar_rad_roll24h'] = df['solar_rad'].rolling(window=4, min_periods=1).mean()
    df['soil_moisture_roll24h'] = df['soil_moisture'].rolling(window=4, min_periods=1).mean()
    df['precip_cum48h'] = df['precip'].rolling(window=8, min_periods=1).sum()

    # Cyclical harmonics
    dayofyear = df['datetime'].dt.dayofyear
    df['sin_hour'] = np.sin(2 * np.pi * df['hour'] / 24.0)
    df['cos_hour'] = np.cos(2 * np.pi * df['hour'] / 24.0)
    df['sin_doy'] = np.sin(2 * np.pi * dayofyear / 365.25)
    df['cos_doy'] = np.cos(2 * np.pi * dayofyear / 365.25)

    # Clean leading boundary NaNs resulting from shifts
    df = df.bfill().reset_index(drop=True)
    return df

def predict_crop_water_footprint_1990_1999():
    """
    Executes blind out-of-sample Crop Water Footprint (CWF) prediction
    for 1990–1999 using the fixed locked-in production model.
    """
    if not os.path.exists(FINAL_MODEL_PATH):
        raise FileNotFoundError(f"Locked production model not found at {FINAL_MODEL_PATH}")

    print("=" * 80)
    print(" BLIND HINDCAST PREDICTION: CROP WATER FOOTPRINT (1990–1999)")
    print("=" * 80)

    # 1. Synthesize input meteorological drivers (without target ET)
    raw_df = generate_1990s_meteorological_inputs(1990, 1999)

    # 2. Engineer features
    df = engineer_features_for_hindcast(raw_df)
    active_features = [f for f in FEATURES if f in df.columns]

    # 3. Load locked production model
    print(f"[Hindcast] Loading locked model from: {FINAL_MODEL_PATH}")
    model = joblib.load(FINAL_MODEL_PATH)

    # 4. Predict Evapotranspiration
    print(f"[Hindcast] Predicting 6-hourly Evapotranspiration for {len(df):,} intervals across 1990–1999...")
    predicted_et = model.predict(df[active_features])
    df['predicted_et_mm'] = np.clip(predicted_et, 0.05, 20.0)

    # 5. Compute Green, Blue, and Total Water Footprints via Calibrator
    calibrator = CropWaterFootprintCalibrator(DEFAULT_CWF_PARAMS)
    
    # Run decade-wide continuous footprint calculation
    cwf_out = calibrator.compute_footprint(
        et_series=df['predicted_et_mm'].values,
        precip_series=df['precip'].values,
        annualize=True
    )

    df['et_crop_adjusted_mm'] = cwf_out['et_c_series']
    df['effective_precip_mm'] = cwf_out['p_eff_series']
    df['et_green_mm'] = cwf_out['et_green_series']
    df['et_blue_mm'] = cwf_out['et_blue_series']

    # 6. Year-by-Year Aggregations
    annual_results = []
    for year in range(1990, 2000):
        yr_sub = df[df['year'] == year]
        yr_cwf = calibrator.compute_footprint(
            et_series=yr_sub['predicted_et_mm'].values,
            precip_series=yr_sub['precip'].values,
            annualize=False
        )
        annual_results.append({
            'year': int(year),
            'sample_count': len(yr_sub),
            'annual_precip_mm': float(yr_sub['precip'].sum()),
            'predicted_annual_et_mm': float(yr_sub['predicted_et_mm'].sum()),
            'green_water_use_m3_ha': float(yr_cwf['cwu_green_m3_ha']),
            'blue_water_use_m3_ha': float(yr_cwf['cwu_blue_m3_ha']),
            'total_water_use_m3_ha': float(yr_cwf['cwu_total_m3_ha']),
            'green_water_footprint_m3_ton': float(yr_cwf['green_water_footprint_m3_ton']),
            'blue_water_footprint_m3_ton': float(yr_cwf['blue_water_footprint_m3_ton']),
            'total_water_footprint_m3_ton': float(yr_cwf['total_water_footprint_m3_ton']),
            'green_water_ratio_pct': float(yr_cwf['green_water_footprint_m3_ton'] / (yr_cwf['total_water_footprint_m3_ton'] + 1e-6) * 100.0)
        })

    annual_summary_df = pd.DataFrame(annual_results)

    # 7. Save outputs to data and outputs folders
    detail_csv = os.path.join(LOCAL_DATA_PATH, "predicted_cwf_1990_1999_timeseries.csv")
    summary_csv = os.path.join(LOCAL_DATA_PATH, "annual_cwf_summary_1990_1999.csv")
    summary_csv_out = os.path.join(OUTPUT_DIR, "annual_cwf_summary_1990_1999.csv")
    
    df.to_csv(detail_csv, index=False)
    annual_summary_df.to_csv(summary_csv, index=False)
    annual_summary_df.to_csv(summary_csv_out, index=False)

    print("\n" + "=" * 90)
    print(f"{'Year':<6} | {'Precip (mm)':<12} | {'Pred ET (mm)':<13} | {'GWF (m³/t)':<12} | {'BWF (m³/t)':<12} | {'Total CWF (m³/t)':<16} | {'Green %'}")
    print("-" * 90)
    for _, row in annual_summary_df.iterrows():
        print(f"{int(row['year']):<6} | {row['annual_precip_mm']:<12.1f} | {row['predicted_annual_et_mm']:<13.1f} | {row['green_water_footprint_m3_ton']:<12.2f} | {row['blue_water_footprint_m3_ton']:<12.2f} | {row['total_water_footprint_m3_ton']:<16.2f} | {row['green_water_ratio_pct']:.1f}%")
    print("=" * 90)

    # Print decade average
    mean_gwf = annual_summary_df['green_water_footprint_m3_ton'].mean()
    mean_bwf = annual_summary_df['blue_water_footprint_m3_ton'].mean()
    mean_twf = annual_summary_df['total_water_footprint_m3_ton'].mean()
    mean_et = annual_summary_df['predicted_annual_et_mm'].mean()
    print(f"\n[Decade 1990–1999 Average Predictions]")
    print(f"  -> Predicted Mean Annual ET:        {mean_et:.1f} mm/year")
    print(f"  -> Green Water Footprint (Rain):     {mean_gwf:.2f} m³/ton ({mean_gwf/mean_twf*100:.1f}%)")
    print(f"  -> Blue Water Footprint (Irrigation):{mean_bwf:.2f} m³/ton ({mean_bwf/mean_twf*100:.1f}%)")
    print(f"  -> Total Crop Water Footprint:       {mean_twf:.2f} m³/ton\n")

    # 8. Visualizations
    plot_1990s_predictions(annual_summary_df, df)

    return annual_summary_df

def plot_1990s_predictions(summary_df, detail_df):
    """Plots the predicted 1990–1999 CWF trajectory and Green/Blue stacked decomposition."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9))

    years = summary_df['year'].values
    gwf = summary_df['green_water_footprint_m3_ton'].values
    bwf = summary_df['blue_water_footprint_m3_ton'].values
    twf = summary_df['total_water_footprint_m3_ton'].values

    # Subplot 1: Stacked Bar Chart of CWF
    ax1.bar(years, gwf, label='Green Water Footprint (Rainfall)', color='#2ca02c', alpha=0.85)
    ax1.bar(years, bwf, bottom=gwf, label='Blue Water Footprint (Irrigation)', color='#1f77b4', alpha=0.85)
    ax1.plot(years, twf, color='black', marker='o', linewidth=2, label='Total CWF (m³/ton)')
    
    ax1.set_title("Blind Hindcast Prediction: Crop Water Footprint by Year (1990–1999)", fontsize=13, fontweight='bold', pad=12)
    ax1.set_ylabel("Water Footprint ($m^3/ton$)", fontsize=11, fontweight='bold')
    ax1.set_xticks(years)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    ax1.legend(loc='upper right')

    for i, yr in enumerate(years):
        ax1.text(yr, twf[i] + 3.0, f"{twf[i]:.1f}", ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Subplot 2: Seasonal ET Prediction Trajectory
    # Resample to monthly average for clean time-series visualization
    monthly = detail_df.set_index('datetime')['predicted_et_mm'].resample('1ME').mean()
    ax2.plot(monthly.index, monthly.values, color='#800080', linewidth=1.8, label='Predicted 6-Hourly ET Monthly Mean (mm)')
    ax2.set_title("Predicted 10-Year Evapotranspiration Seasonal Cycle (1990–1999)", fontsize=12, fontweight='bold')
    ax2.set_ylabel("Evapotranspiration ($mm$)", fontsize=11, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='upper right')

    plt.tight_layout()
    chart_path = os.path.join(OUTPUT_DIR, "cwf_prediction_1990_1999.png")
    plt.savefig(chart_path, dpi=300)
    print(f"[Hindcast] Visual chart saved to: {chart_path}")
    plt.close()

if __name__ == "__main__":
    predict_crop_water_footprint_1990_1999()
