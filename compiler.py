import glob
import os
import pandas as pd
import numpy as np
from config import LOCAL_DATA_PATH, FEATURES, TARGET, BASE_FEATURES, LAG_FEATURES

def compile_datasets(data_dir=LOCAL_DATA_PATH):
    """
    Compiles individual annual 6-hourly CSV files into a unified, cleaned,
    chronologically sorted DataFrame with engineered lag features.
    
    Returns:
        pd.DataFrame or None: Cleaned and structured DataFrame ready for ML modeling.
    """
    pattern = os.path.join(data_dir, "cwf_6hourly_*.csv")
    all_files = glob.glob(pattern)
    
    if not all_files:
        master_file = os.path.join(data_dir, "master_engineered_dataset.csv")
        if os.path.exists(master_file):
            print(f"[Compiler] Loading cached master dataset from: {master_file}")
            df = pd.read_csv(master_file)
            df['datetime'] = pd.to_datetime(df['datetime'])
            return df
        print(f"[Compiler] No files found matching {pattern}.")
        print("[Compiler] Please wait for GEE tasks to finish exporting and place CSVs into the local data directory, or run mock_data_generator.py.")
        return None

    print(f"[Compiler] Found {len(all_files)} CSV files. Ingesting...")
    df_list = []
    for f in all_files:
        try:
            temp_df = pd.read_csv(f)
            df_list.append(temp_df)
        except Exception as err:
            print(f"[Compiler] Warning: Could not read {f}: {err}")

    if not df_list:
        return None

    master_df = pd.concat(df_list, ignore_index=True)
    
    # Standardize and sort datetime
    master_df['datetime'] = pd.to_datetime(master_df['datetime'])
    master_df = master_df.sort_values(by='datetime').reset_index(drop=True)
    
    # Replace Earth Engine null/placeholder values (-9999) with NaN
    master_df = master_df.replace(-9999, np.nan)
    master_df = master_df.replace(-9999.0, np.nan)
    
    # Interpolate minor missing intervals or drop unrecoverable records
    for col in BASE_FEATURES:
        if col in master_df.columns:
            master_df[col] = pd.to_numeric(master_df[col], errors='coerce')
            master_df[col] = master_df[col].interpolate(method='linear', limit=2)
            
    if TARGET in master_df.columns:
        master_df[TARGET] = pd.to_numeric(master_df[TARGET], errors='coerce')
        master_df[TARGET] = master_df[TARGET].interpolate(method='linear', limit=2)

    # Compute temporal lag features (1 step = 6h, 4 steps = 24h prior)
    lag_mapping = {
        'temp_c_lag1': ('temp_c', 1),
        'precip_lag1': ('precip', 1),
        'ndvi_lag1': ('ndvi', 1),
        'soil_moisture_lag1': ('soil_moisture', 1),
        'temp_c_lag4': ('temp_c', 4),
        'soil_moisture_lag4': ('soil_moisture', 4)
    }
    for lag_col, (base_col, shift_n) in lag_mapping.items():
        if base_col in master_df.columns:
            master_df[lag_col] = master_df[base_col].shift(shift_n)

    # Rolling window aggregated statistics (24h = 4 steps, 48h = 8 steps)
    if 'temp_c' in master_df.columns:
        master_df['temp_c_roll24h'] = master_df['temp_c'].rolling(window=4, min_periods=1).mean()
    if 'solar_rad' in master_df.columns:
        master_df['solar_rad_roll24h'] = master_df['solar_rad'].rolling(window=4, min_periods=1).mean()
    if 'soil_moisture' in master_df.columns:
        master_df['soil_moisture_roll24h'] = master_df['soil_moisture'].rolling(window=4, min_periods=1).mean()
    if 'precip' in master_df.columns:
        master_df['precip_cum48h'] = master_df['precip'].rolling(window=8, min_periods=1).sum()

    # Cyclical temporal harmonics (capturing diurnal & seasonal cycles)
    master_df['year'] = master_df['datetime'].dt.year
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

    # Save compiled master engineered dataset to data directory for future training
    master_save_path = os.path.join(data_dir, "master_engineered_dataset.csv")
    try:
        master_df.to_csv(master_save_path, index=False)
        print(f"[Compiler] Saved compiled master engineered dataset to: {master_save_path}")
    except Exception as e:
        print(f"[Compiler] Notice: Could not write {master_save_path}: {e}")

    print(f"[Compiler] SUCCESS: Compiled master dataset with {len(master_df):,} records ({len(active_cols)} active features) across {len(master_df['year'].unique())} years ({master_df['year'].min()} to {master_df['year'].max()}).")
    return master_df

if __name__ == "__main__":
    df = compile_datasets()
    if df is not None:
        print(df.head())
        print(df.info())
