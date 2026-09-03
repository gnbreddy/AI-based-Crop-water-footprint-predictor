import os
import argparse
import pandas as pd
import numpy as np
from config import LOCAL_DATA_PATH, BASE_FEATURES, TARGET, REGIONS

def simulate_region_meteorology(region_key: str, date_rng: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Simulates physics-grounded 6-hourly climate and satellite variables for a specific agro-ecological region.
    """
    n_samples = len(date_rng)
    df = pd.DataFrame({'datetime': date_rng})
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    df['day'] = df['datetime'].dt.day
    df['hour'] = df['datetime'].dt.hour
    df['system:time_start'] = df['datetime'].astype('int64') // 10**6
    df['region'] = region_key

    day_of_year = df['datetime'].dt.dayofyear.values
    hour_of_day = df['hour'].values
    solar_base = np.maximum(0, np.sin(np.pi * (hour_of_day - 6) / 12))

    if region_key == 'nile_delta':
        # Egypt: Hyper-arid, hot summer (36-40C), mild winter (16-19C), near zero rain, intense solar
        temp_annual = 27.0 + 11.0 * np.sin(2 * np.pi * (day_of_year - 105) / 365)
        temp_diurnal = 7.0 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        df['temp_c'] = temp_annual + temp_diurnal + np.random.normal(0, 1.2, n_samples)

        df['wind_speed'] = np.clip(3.8 + 1.0 * np.sin(2 * np.pi * day_of_year / 365) + np.random.exponential(1.2, n_samples), 0.8, 18.0)
        df['pressure_kpa'] = 101.0 + 0.5 * np.cos(2 * np.pi * day_of_year / 365) + np.random.normal(0, 0.2, n_samples)

        # Clear skies solar radiation
        df['solar_rad'] = solar_base * (22.0 + 4.0 * np.cos(2 * np.pi * (day_of_year - 172) / 365)) + np.random.uniform(0, 0.8, n_samples)

        # Rain: Very rare (mostly 0.0)
        rain_prob = np.where((day_of_year <= 45) | (day_of_year >= 330), 0.03, 0.002)
        rain_event = np.random.binomial(1, rain_prob, n_samples)
        df['precip'] = rain_event * np.random.gamma(shape=1.5, scale=1.5, size=n_samples)

        # Soil moisture: Controlled by irrigation canals, low natural
        df['soil_moisture'] = np.clip(0.12 + 0.08 * np.sin(2 * np.pi * (day_of_year - 150) / 365) + np.random.normal(0, 0.015, n_samples), 0.06, 0.30)

        # Cotton crop cycle: Peak greening in June-August (days 160-240)
        df['ndvi'] = np.clip(0.20 + 0.45 * np.exp(-((day_of_year - 200) ** 2) / (2 * 45 ** 2)) + np.random.normal(0, 0.02, n_samples), 0.12, 0.78)

        latent_et = 0.09 * df['temp_c'] + 0.14 * df['solar_rad'] + 3.8 * df['soil_moisture'] + 2.2 * df['ndvi'] + 0.06 * df['wind_speed']

    elif region_key == 'kansas':
        # USA Great Plains: Continental extremes (-5C to +33C), convective spring rains, winter freeze
        temp_annual = 14.0 + 17.0 * np.sin(2 * np.pi * (day_of_year - 110) / 365)
        temp_diurnal = 8.0 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        df['temp_c'] = temp_annual + temp_diurnal + np.random.normal(0, 2.0, n_samples)

        df['wind_speed'] = np.clip(4.8 + 1.8 * np.sin(2 * np.pi * day_of_year / 365) + np.random.exponential(1.8, n_samples), 1.0, 25.0)
        df['pressure_kpa'] = 96.0 + 0.8 * np.cos(2 * np.pi * day_of_year / 365) + np.random.normal(0, 0.4, n_samples)

        df['solar_rad'] = solar_base * (16.0 + 7.0 * np.cos(2 * np.pi * (day_of_year - 172) / 365)) + np.random.uniform(0, 1.0, n_samples)

        # Spring convective rains (days 90-190)
        is_spring_rain = (day_of_year >= 85) & (day_of_year <= 195)
        rain_prob = np.where(is_spring_rain, 0.28, 0.08)
        rain_event = np.random.binomial(1, rain_prob, n_samples)
        df['precip'] = rain_event * np.random.gamma(shape=2.2, scale=3.5, size=n_samples)

        df['soil_moisture'] = np.clip(0.24 + 0.10 * np.sin(2 * np.pi * (day_of_year - 90) / 365) + (df['precip'] * 0.012) + np.random.normal(0, 0.02, n_samples), 0.10, 0.40)

        # Winter wheat peak in May (days 120-160), ripening / harvest in June
        df['ndvi'] = np.clip(0.25 + 0.50 * np.exp(-((day_of_year - 140) ** 2) / (2 * 40 ** 2)) + np.random.normal(0, 0.03, n_samples), 0.15, 0.85)

        latent_et = 0.08 * np.maximum(0, df['temp_c']) + 0.12 * df['solar_rad'] + 4.2 * df['soil_moisture'] + 2.6 * df['ndvi'] + 0.05 * df['wind_speed']

    elif region_key == 'mekong_delta':
        # Vietnam: Tropical monsoon, year-round warm (27-31C), intense rainy season (May-Nov), high humidity
        temp_annual = 28.5 + 2.5 * np.sin(2 * np.pi * (day_of_year - 90) / 365)
        temp_diurnal = 3.5 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        df['temp_c'] = temp_annual + temp_diurnal + np.random.normal(0, 1.0, n_samples)

        df['wind_speed'] = np.clip(2.8 + 1.0 * np.sin(2 * np.pi * day_of_year / 365) + np.random.exponential(1.0, n_samples), 0.5, 15.0)
        df['pressure_kpa'] = 101.1 + 0.3 * np.cos(2 * np.pi * day_of_year / 365) + np.random.normal(0, 0.2, n_samples)

        # Monsoon cloudiness dampens peak solar
        df['solar_rad'] = solar_base * (16.5 + 3.0 * np.cos(2 * np.pi * (day_of_year - 120) / 365)) + np.random.uniform(0, 1.2, n_samples)

        # Heavy monsoon rain May-Nov (days 130-320)
        is_wet_season = (day_of_year >= 130) & (day_of_year <= 320)
        rain_prob = np.where(is_wet_season, 0.45, 0.10)
        rain_event = np.random.binomial(1, rain_prob, n_samples)
        df['precip'] = rain_event * np.random.gamma(shape=2.5, scale=5.5, size=n_samples)

        # Saturated paddy soil moisture
        df['soil_moisture'] = np.clip(0.32 + 0.10 * np.sin(2 * np.pi * (day_of_year - 160) / 365) + (df['precip'] * 0.015) + np.random.normal(0, 0.02, n_samples), 0.18, 0.48)

        # Double / triple paddy rice vegetation cycles
        rice_cycle = 0.25 * np.sin(4 * np.pi * day_of_year / 365) ** 2 + 0.25 * np.sin(2 * np.pi * day_of_year / 365) ** 2
        df['ndvi'] = np.clip(0.30 + rice_cycle + np.random.normal(0, 0.03, n_samples), 0.20, 0.85)

        latent_et = 0.07 * df['temp_c'] + 0.13 * df['solar_rad'] + 4.5 * df['soil_moisture'] + 2.8 * df['ndvi'] + 0.04 * df['wind_speed']

    else:
        # Default Kolhapur (India) - Sugarcane / Western Ghats monsoon
        temp_annual = 26.0 + 8.0 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        temp_diurnal = 5.0 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        df['temp_c'] = temp_annual + temp_diurnal + np.random.normal(0, 1.5, n_samples)

        df['wind_speed'] = np.clip(3.5 + 1.5 * np.sin(2 * np.pi * day_of_year / 365) + np.random.exponential(1.5, n_samples), 0.5, 20.0)
        df['pressure_kpa'] = 98.5 + 1.0 * np.cos(2 * np.pi * day_of_year / 365) + np.random.normal(0, 0.3, n_samples)

        df['solar_rad'] = solar_base * (18.0 + 5.0 * np.cos(2 * np.pi * (day_of_year - 172) / 365)) + np.random.uniform(0, 1.0, n_samples)

        # Monsoon (days 150-270)
        is_monsoon = (day_of_year >= 150) & (day_of_year <= 270)
        rain_prob = np.where(is_monsoon, 0.35, 0.05)
        rain_event = np.random.binomial(1, rain_prob, n_samples)
        df['precip'] = rain_event * np.random.gamma(shape=2.0, scale=4.0, size=n_samples)

        df['soil_moisture'] = np.clip(0.15 + 0.15 * np.sin(2 * np.pi * (day_of_year - 140) / 365) + (df['precip'] * 0.01) + np.random.normal(0, 0.02, n_samples), 0.08, 0.48)
        df['ndvi'] = np.clip(0.35 + 0.35 * np.sin(2 * np.pi * (day_of_year - 180) / 365) + np.random.normal(0, 0.03, n_samples), 0.1, 0.9)

        latent_et = 0.08 * df['temp_c'] + 0.12 * df['solar_rad'] + 4.0 * df['soil_moisture'] + 2.5 * df['ndvi'] + 0.05 * df['wind_speed']

    df[TARGET] = np.clip(latent_et + np.random.normal(0, 0.15, n_samples), 0.1, 15.0)
    return df

def generate_mock_data(start_year=2000, end_year=2025, data_dir=LOCAL_DATA_PATH, regions=None):
    """
    Generates realistic synthetic 6-hourly meteorological and satellite observation data
    across target agricultural regions (Kolhapur, Nile Delta, Kansas, Mekong Delta).
    """
    os.makedirs(data_dir, exist_ok=True)
    np.random.seed(42)

    if regions is None:
        regions = list(REGIONS.keys())
    elif isinstance(regions, str):
        regions = [regions]

    generated_files = []
    print(f"[Mock Generator] Generating multi-region datasets ({start_year} -> {end_year}) for {len(regions)} regions in: {data_dir}")

    for region_key in regions:
        reg_name = REGIONS.get(region_key, {}).get('name', region_key)
        print(f"\n--- Simulating Region: {reg_name} ---")
        for year in range(start_year, end_year + 1):
            date_rng = pd.date_range(
                start=f'{year}-01-01 00:00:00',
                end=f'{year}-12-31 18:00:00',
                freq='6h'
            )
            df = simulate_region_meteorology(region_key, date_rng)

            # Save region-specific file
            reg_file_path = os.path.join(data_dir, f'cwf_6hourly_{region_key}_{year}.csv')
            df.to_csv(reg_file_path, index=False)
            generated_files.append(reg_file_path)

            # For backward compatibility with legacy single-region pipeline for Kolhapur
            if region_key == 'kolhapur':
                legacy_file_path = os.path.join(data_dir, f'cwf_6hourly_{year}.csv')
                df.to_csv(legacy_file_path, index=False)

            if year in [start_year, end_year] or year % 5 == 0:
                print(f"  [+] Created {os.path.basename(reg_file_path)} ({len(df):,} rows)")

    print(f"\n[Mock Generator] Successfully generated {len(generated_files)} regional files.\n")
    return generated_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic multi-location datasets for offline training")
    parser.add_argument("--start-year", type=int, default=2020)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--region", type=str, default="all", choices=list(REGIONS.keys()) + ["all"])
    args = parser.parse_args()

    selected_regions = list(REGIONS.keys()) if args.region == "all" else [args.region]
    generate_mock_data(start_year=args.start_year, end_year=args.end_year, regions=selected_regions)

