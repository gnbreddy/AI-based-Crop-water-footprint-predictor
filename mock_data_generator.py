import os
import pandas as pd
import numpy as np
from config import LOCAL_DATA_PATH, BASE_FEATURES, TARGET

def generate_mock_data(start_year=2000, end_year=2025, data_dir=LOCAL_DATA_PATH):
    """
    Generates realistic synthetic 6-hourly meteorological and satellite observation data
    mimicking ERA5-Land, CHIRPS, and MODIS collections for local offline pipeline testing
    across the full multi-decade period (2000–2025).
    
    Args:
        start_year (int): First year to generate (default 2000).
        end_year (int): Final year to generate (default 2025).
        data_dir (str): Destination folder for CSV files.
    """
    os.makedirs(data_dir, exist_ok=True)
    np.random.seed(42)

    generated_files = []
    print(f"[Mock Generator] Generating synthetic dataset ({start_year} -> {end_year}) in: {data_dir}")

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

        # Seasonal and diurnal physics simulation
        day_of_year = df['datetime'].dt.dayofyear.values
        hour_of_day = df['hour'].values

        # Temperature: Annual + Diurnal sinusoidal variation
        temp_annual = 26.0 + 8.0 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        temp_diurnal = 5.0 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        df['temp_c'] = temp_annual + temp_diurnal + np.random.normal(0, 1.5, n_samples)

        # Wind speed (m/s)
        df['wind_speed'] = np.clip(3.5 + 1.5 * np.sin(2 * np.pi * day_of_year / 365) + np.random.exponential(1.5, n_samples), 0.5, 20.0)

        # Surface pressure (kPa)
        df['pressure_kpa'] = 98.5 + 1.0 * np.cos(2 * np.pi * day_of_year / 365) + np.random.normal(0, 0.3, n_samples)

        # Solar Radiation (MJ/m2): Peak around noon, 0 at night
        solar_base = np.maximum(0, np.sin(np.pi * (hour_of_day - 6) / 12))
        df['solar_rad'] = solar_base * (18.0 + 5.0 * np.cos(2 * np.pi * (day_of_year - 172) / 365)) + np.random.uniform(0, 1.0, n_samples)

        # Monsoon Precipitation (mm) (Peak in June-Sept: days 150-270)
        is_monsoon = (day_of_year >= 150) & (day_of_year <= 270)
        rain_prob = np.where(is_monsoon, 0.35, 0.05)
        rain_event = np.random.binomial(1, rain_prob, n_samples)
        df['precip'] = rain_event * np.random.gamma(shape=2.0, scale=4.0, size=n_samples)

        # Soil moisture (m3/m3) (0.10 to 0.45, responds to precip)
        base_sm = 0.15 + (0.20 if is_monsoon.any() else 0.0)
        df['soil_moisture'] = np.clip(0.15 + 0.15 * np.sin(2 * np.pi * (day_of_year - 140) / 365) + (df['precip'] * 0.01) + np.random.normal(0, 0.02, n_samples), 0.08, 0.48)

        # NDVI (0.25 to 0.85, vegetation greening after rains)
        df['ndvi'] = np.clip(0.35 + 0.35 * np.sin(2 * np.pi * (day_of_year - 180) / 365) + np.random.normal(0, 0.03, n_samples), 0.1, 0.9)

        # MODIS ET target (mm/6h) (Strong physical correlation with Solar, Temp, Soil Moisture, NDVI)
        latent_et = (
            0.08 * df['temp_c'] +
            0.12 * df['solar_rad'] +
            4.0 * df['soil_moisture'] +
            2.5 * df['ndvi'] +
            0.05 * df['wind_speed'] +
            np.random.normal(0, 0.2, n_samples)
        )
        df[TARGET] = np.clip(latent_et, 0.1, 15.0)

        # Save to CSV
        file_path = os.path.join(data_dir, f'cwf_6hourly_{year}.csv')
        df.to_csv(file_path, index=False)
        generated_files.append(file_path)
        print(f"  [+] Created {file_path} ({len(df):,} rows)")

    print(f"[Mock Generator] Successfully generated {len(generated_files)} files.\n")
    return generated_files

if __name__ == "__main__":
    generate_mock_data()
