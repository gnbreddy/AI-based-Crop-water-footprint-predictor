import glob
import os
import pandas as pd
import numpy as np
from config import LOCAL_DATA_PATH, FEATURES, TARGET, BASE_FEATURES, LAG_FEATURES, BIOPHYSICAL_FEATURES, EXTENDED_FEATURES, DATASET_REGIMES

def compile_datasets(data_dir=LOCAL_DATA_PATH):
    """
    Compiles individual annual CSV files across regions into a unified,
    cleaned, chronologically sorted DataFrame with engineered biophysical,
    lag, and rolling features computed independently per region.
    
    Returns:
        pd.DataFrame or None: Cleaned and structured DataFrame ready for ML modeling.
    """
    # Discover all authentic epoch CSVs: cwf_kolhapur_*.csv, cwf_epoch_*.csv, and cwf_6hourly_*.csv
    kolhapur_files = glob.glob(os.path.join(data_dir, "cwf_kolhapur_*.csv"))
    epoch_files = glob.glob(os.path.join(data_dir, "cwf_epoch_*.csv"))
    hourly_files = glob.glob(os.path.join(data_dir, "cwf_6hourly_*.csv"))
    all_files = sorted(kolhapur_files if kolhapur_files else (epoch_files if epoch_files else hourly_files))
    
    if not all_files:
        master_file = os.path.join(data_dir, "master_engineered_dataset.csv")
        if os.path.exists(master_file):
            print(f"[Compiler] Loading cached master dataset from: {master_file}")
            df = pd.read_csv(master_file)
            df['datetime'] = pd.to_datetime(df['datetime'])
            return df
        print(f"[Compiler] No GEE epoch files found in {data_dir}.")
        print("[Compiler] Please extract data using: python extractor.py --start-year 2000 --end-year 2025")
        return None

    files_to_load = all_files

    print(f"[Compiler] Found {len(files_to_load)} relevant CSV files. Ingesting...")
    df_list = []
    for f in files_to_load:
        try:
            temp_df = pd.read_csv(f)
            fname = os.path.basename(f)
            # Infer region from filename if not in columns
            if 'region' not in temp_df.columns:
                inferred_region = 'kolhapur'
                for reg in ['kolhapur', 'karveer', 'shirol', 'radhanagari', 'kagal', 'hatkanangale']:
                    if reg in fname:
                        inferred_region = reg
                        break
            else:
                inferred_region = temp_df['region'].iloc[0] if not temp_df.empty else 'kolhapur'
            temp_df['region'] = inferred_region
            df_list.append(temp_df)
        except Exception as err:
            print(f"[Compiler] Warning: Could not read {f}: {err}")

    if not df_list:
        return None

    master_raw = pd.concat(df_list, ignore_index=True)
    master_raw['datetime'] = pd.to_datetime(master_raw['datetime'], errors='coerce')
    master_raw = master_raw.dropna(subset=['datetime']).reset_index(drop=True)

    
    # Replace Earth Engine null/placeholder values (-9999) with NaN
    master_raw = master_raw.replace(-9999, np.nan)
    master_raw = master_raw.replace(-9999.0, np.nan)
    
    # Keep simultaneous observations from separate monitoring stations. Using
    # only region + datetime collapsed five Kolhapur nodes into one record.
    identity_cols = ['region', 'station_node', 'datetime'] if 'station_node' in master_raw.columns else ['region', 'datetime']
    master_raw = master_raw.drop_duplicates(subset=identity_cols).reset_index(drop=True)

    # Calculate temporal features independently per station, preventing lags
    # from crossing station boundaries.
    regional_processed_dfs = []
    group_cols = ['region', 'station_node'] if 'station_node' in master_raw.columns else ['region']
    
    lag_mapping = {
        'temp_c_lag1': ('temp_c', 1),
        'precip_lag1': ('precip', 1),
        'ndvi_lag1': ('ndvi', 1),
        'soil_moisture_lag1': ('soil_moisture', 1),
        'temp_c_lag4': ('temp_c', 4),
        'soil_moisture_lag4': ('soil_moisture', 4)
    }

    for _, station_df in master_raw.groupby(group_cols, sort=False):
        sub_df = station_df.copy()
        sub_df = sub_df.sort_values(by='datetime').reset_index(drop=True)

        # Standardize soil moisture column if multiple layer columns exist
        if 'soil_moisture' not in sub_df.columns:
            if 'soil_moisture_root' in sub_df.columns:
                sub_df['soil_moisture'] = sub_df['soil_moisture_root']
            elif 'soil_moisture_layer2' in sub_df.columns:
                sub_df['soil_moisture'] = sub_df['soil_moisture_layer2']

        # Preserve the independently observed MODIS ET target whenever present.
        # The calculated crop-ET field is suitable only as a fallback; replacing
        # MODIS ET with it makes validation measure a formula surrogate instead
        # of unseen satellite observations.
        if TARGET not in sub_df.columns or sub_df[TARGET].isna().all():
            if 'et_crop_mm' in sub_df.columns and not sub_df['et_crop_mm'].isna().all():
                sub_df[TARGET] = sub_df['et_crop_mm']
            elif 'et0_fao56_mm' in sub_df.columns:
                sub_df[TARGET] = sub_df['et0_fao56_mm'] * 0.50


        for col in BASE_FEATURES:
            if col in sub_df.columns:
                sub_df[col] = pd.to_numeric(sub_df[col], errors='coerce')
                sub_df[col] = sub_df[col].interpolate(method='linear', limit=2)
                
        if TARGET in sub_df.columns:
            sub_df[TARGET] = pd.to_numeric(sub_df[TARGET], errors='coerce')
            sub_df[TARGET] = sub_df[TARGET].interpolate(method='linear', limit=2)

        # Compute temporal lag features per region
        for lag_col, (base_col, shift_n) in lag_mapping.items():
            if base_col in sub_df.columns:
                sub_df[lag_col] = sub_df[base_col].shift(shift_n)

        # Rolling window aggregated statistics per region (24h = 4 steps, 48h = 8 steps)
        if 'temp_c' in sub_df.columns:
            sub_df['temp_c_roll24h'] = sub_df['temp_c'].rolling(window=4, min_periods=1).mean()
        if 'solar_rad' in sub_df.columns:
            sub_df['solar_rad_roll24h'] = sub_df['solar_rad'].rolling(window=4, min_periods=1).mean()
        if 'soil_moisture' in sub_df.columns:
            sub_df['soil_moisture_roll24h'] = sub_df['soil_moisture'].rolling(window=4, min_periods=1).mean()
        if 'precip' in sub_df.columns:
            sub_df['precip_cum48h'] = sub_df['precip'].rolling(window=8, min_periods=1).sum()

        # ======================================================================
        # BIOPHYSICAL & PLANT PHYSIOLOGY FEATURE ENGINEERING (Zero-Negative-Effect)
        # ======================================================================
        # 1. Growing Degree Days (GDD) with T_base = 12.0°C for sugarcane
        t_base = 12.0
        temp_col = sub_df['temp_c'] if 'temp_c' in sub_df.columns else pd.Series(25.0, index=sub_df.index)
        sub_df['gdd_step'] = np.maximum(0.0, temp_col - t_base) * (3.0 / 24.0)
        sub_df['year'] = sub_df['datetime'].dt.year
        sub_df['gdd_cum'] = sub_df.groupby('year')['gdd_step'].cumsum()

        # 2. Dynamic Root Depth Zr(t) expanding from 0.20m to 1.20m based on thermal time
        sub_df['dynamic_root_depth'] = 0.20 + (1.20 - 0.20) * np.clip(sub_df['gdd_cum'] / 1800.0, 0.0, 1.0)

        # 3. Dual Crop Coefficient (Kc = Kcb + Ke)
        if 'ndvi' in sub_df.columns:
            sub_df['kcb'] = np.clip(0.15 + 1.10 * (sub_df['ndvi'] - 0.15) / (0.75 - 0.15 + 1e-6), 0.15, 1.25)
        else:
            sub_df['kcb'] = 0.50

        # Surface evaporation Ke driven by upper soil moisture layer
        surf_sm = sub_df['soil_moisture_layer1'] if 'soil_moisture_layer1' in sub_df.columns else sub_df['soil_moisture']
        sub_df['ke'] = np.clip(0.50 * surf_sm * (1.0 - sub_df['kcb'] / 1.4), 0.02, 0.80)
        sub_df['kc_dual'] = np.clip(sub_df['kcb'] + sub_df['ke'], 0.15, 1.45)

        # 4. Jarvis-Stewart Stomatal Closure Attenuation Factor (VPD > 2.2 kPa)
        vpd_col = sub_df['vpd_kpa'] if 'vpd_kpa' in sub_df.columns else pd.Series(1.15, index=sub_df.index)
        sub_df['f_vpd_attenuation'] = np.clip(1.0 - 0.35 * np.maximum(0.0, vpd_col - 2.2), 0.25, 1.0)

        # 5. Flash Drought Atmospheric Thirst Index (VPD / Root Soil Moisture)
        sm_root_col = sub_df['soil_moisture_root'] if 'soil_moisture_root' in sub_df.columns else sub_df['soil_moisture']
        sub_df['flash_drought_idx'] = np.clip(vpd_col / (sm_root_col + 1e-4), 0.0, 50.0)

        # 6. Waterlogging & Root Asphyxiation Flood Saturation Index
        precip_48h = sub_df['precip_cum48h'] if 'precip_cum48h' in sub_df.columns else pd.Series(0.0, index=sub_df.index)
        sub_df['flood_saturation_idx'] = np.clip((precip_48h / 40.0) * (sub_df['soil_moisture'] / 0.32), 0.0, 5.0)

        regional_processed_dfs.append(sub_df)


    master_df = pd.concat(regional_processed_dfs, ignore_index=True)

    # Cyclical temporal harmonics
    master_df['year'] = master_df['datetime'].dt.year
    # Keep the observed target-distribution break visible to downstream audits.
    # These labels deliberately do not assert that any societal event caused it.
    master_df['dataset_regime'] = np.select(
        [
            master_df['year'].isin(DATASET_REGIMES['observed_target_regime_pre_2020']),
            master_df['year'].isin(DATASET_REGIMES['observed_target_transition_2020']),
        ],
        ['observed_target_regime_pre_2020', 'observed_target_transition_2020'],
        default='observed_target_regime_post_2020'
    )
    master_df['month'] = master_df['datetime'].dt.month
    master_df['day'] = master_df['datetime'].dt.day
    master_df['hour'] = master_df['datetime'].dt.hour
    dayofyear = master_df['datetime'].dt.dayofyear

    master_df['sin_hour'] = np.sin(2 * np.pi * master_df['hour'] / 24.0)
    master_df['cos_hour'] = np.cos(2 * np.pi * master_df['hour'] / 24.0)
    master_df['sin_doy'] = np.sin(2 * np.pi * dayofyear / 365.25)
    master_df['cos_doy'] = np.cos(2 * np.pi * dayofyear / 365.25)

    if 'system:time_start' not in master_df.columns:
        master_df['system:time_start'] = master_df['datetime'].astype('int64') // 10**6

    # Drop residual NaN rows resulting from lag shifting
    active_cols = [c for c in FEATURES if c in master_df.columns] + ([TARGET] if TARGET in master_df.columns else [])
    master_df = master_df.dropna(subset=active_cols).reset_index(drop=True)

    # Save compiled master engineered dataset to data directory
    master_save_path = os.path.join(data_dir, "master_engineered_dataset.csv")
    try:
        master_df.to_csv(master_save_path, index=False)
        print(f"[Compiler] Saved compiled master engineered dataset to: {master_save_path}")
    except Exception as e:
        print(f"[Compiler] Notice: Could not write {master_save_path}: {e}")

    region_summary = master_df['region'].value_counts().to_dict() if 'region' in master_df.columns else {'default': len(master_df)}
    print(f"[Compiler] SUCCESS: Compiled master dataset with {len(master_df):,} records across {len(master_df['year'].unique())} years ({master_df['year'].min()} to {master_df['year'].max()}). Regions: {region_summary}")
    return master_df

if __name__ == "__main__":
    df = compile_datasets()
    if df is not None:
        print(df.head())
        print(df.info())
