import glob
import os
import pandas as pd
import numpy as np
from config import LOCAL_DATA_PATH, FEATURES, TARGET, BASE_FEATURES, LAG_FEATURES

def compile_datasets(data_dir=LOCAL_DATA_PATH):
    """
    Compiles individual annual 6-hourly CSV files across regions into a unified,
    cleaned, chronologically sorted DataFrame with engineered lag and rolling features
    computed independently per region.
    
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

    # Filter out duplicate kolhapur files if both cwf_6hourly_<year>.csv and cwf_6hourly_kolhapur_<year>.csv exist
    regional_files = [f for f in all_files if any(k in os.path.basename(f) for k in ['kolhapur', 'nile_delta', 'kansas', 'mekong_delta'])]
    files_to_load = regional_files if len(regional_files) > 0 else all_files

    print(f"[Compiler] Found {len(files_to_load)} relevant CSV files. Ingesting...")
    df_list = []
    for f in files_to_load:
        try:
            temp_df = pd.read_csv(f)
            fname = os.path.basename(f)
            # Infer region from filename if not in columns
            if 'region' not in temp_df.columns:
                inferred_region = 'kolhapur'
                for reg in ['kolhapur', 'nile_delta', 'kansas', 'mekong_delta']:
                    if reg in fname:
                        inferred_region = reg
                        break
                temp_df['region'] = inferred_region
            df_list.append(temp_df)
        except Exception as err:
            print(f"[Compiler] Warning: Could not read {f}: {err}")

    if not df_list:
        return None

    master_raw = pd.concat(df_list, ignore_index=True)
    master_raw['datetime'] = pd.to_datetime(master_raw['datetime'])
    
    # Replace Earth Engine null/placeholder values (-9999) with NaN
    master_raw = master_raw.replace(-9999, np.nan)
    master_raw = master_raw.replace(-9999.0, np.nan)
    
    # Deduplicate across region and datetime
    if 'region' in master_raw.columns:
        master_raw = master_raw.drop_duplicates(subset=['region', 'datetime']).reset_index(drop=True)
    else:
        master_raw = master_raw.drop_duplicates(subset=['datetime']).reset_index(drop=True)

    # Process lag and rolling features partitioned by region
    regional_processed_dfs = []
    regions = master_raw['region'].unique() if 'region' in master_raw.columns else ['kolhapur']
    
    lag_mapping = {
        'temp_c_lag1': ('temp_c', 1),
        'precip_lag1': ('precip', 1),
        'ndvi_lag1': ('ndvi', 1),
        'soil_moisture_lag1': ('soil_moisture', 1),
        'temp_c_lag4': ('temp_c', 4),
        'soil_moisture_lag4': ('soil_moisture', 4)
    }

    for reg in regions:
        sub_df = master_raw[master_raw['region'] == reg].copy() if 'region' in master_raw.columns else master_raw.copy()
        sub_df = sub_df.sort_values(by='datetime').reset_index(drop=True)

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

        regional_processed_dfs.append(sub_df)

    master_df = pd.concat(regional_processed_dfs, ignore_index=True)

    # Cyclical temporal harmonics
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
