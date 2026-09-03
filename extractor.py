import os
import argparse
import pandas as pd
import ee
from config import GEE_PROJECT_ID, ROI_COORDS, DATA_EXPORT_FOLDER, REGIONS, LOCAL_DATA_PATH

def authenticate_gee():
    """Authenticates and initializes Google Earth Engine with the configured project ID."""
    try:
        ee.Initialize(project=GEE_PROJECT_ID)
        print(f"GEE Initialized Successfully with project: {GEE_PROJECT_ID}")
        return True
    except Exception as e:
        print(f"Error initializing GEE: {e}. Attempting interactive re-authentication...")
        try:
            ee.Authenticate()
            ee.Initialize(project=GEE_PROJECT_ID)
            print("GEE Re-initialized Successfully after authentication!")
            return True
        except Exception as auth_err:
            print(f"Failed to authenticate with GEE: {auth_err}")
            return False

def get_region_metadata(region_key: str):
    """Retrieves bounding box and metadata for a given region key."""
    norm_key = region_key.lower().strip()
    if norm_key in REGIONS:
        return norm_key, REGIONS[norm_key]
    
    # Check partial matches
    for k, v in REGIONS.items():
        if norm_key in k or k in norm_key:
            return k, v
            
    print(f"[Extractor] Unknown region '{region_key}'. Defaulting to 'kolhapur'.")
    return 'kolhapur', REGIONS['kolhapur']

def extract_6hourly_data_for_year(year: int, region: str = 'kolhapur'):
    """
    Extracts 6-hourly aggregated meteorological and remote sensing features for a given year
    over the chosen Region of Interest (ROI) and submits an Earth Engine batch export task to Google Drive.
    """
    reg_key, reg_info = get_region_metadata(region)
    roi_coords = reg_info['roi_coords']
    roi = ee.Geometry.Rectangle(roi_coords)
    
    start_date = ee.Date.fromYMD(year, 1, 1)
    end_date = ee.Date.fromYMD(year + 1, 1, 1)
    total_hours = end_date.difference(start_date, 'hour')
    step_hours = ee.List.sequence(0, total_hours.subtract(1), 6)

    def extract_time_step(h):
        t = start_date.advance(h, 'hour')
        
        # ERA5-Land hourly meteorological data
        era5 = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").filterDate(t, t.advance(1, 'hour')).first()
        temp_c = era5.select('temperature_2m').subtract(273.15).rename('temp_c')
        wind = era5.expression(
            'sqrt(u**2 + v**2)',
            {
                'u': era5.select('u_component_of_wind_10m'),
                'v': era5.select('v_component_of_wind_10m')
            }
        ).rename('wind_speed')
        press = era5.select('surface_pressure').divide(1000).rename('pressure_kpa')
        solar = era5.select('surface_solar_radiation_downwards').divide(1000000).rename('solar_rad')
        sm = era5.select('volumetric_soil_water_layer_1').rename('soil_moisture')

        # CHIRPS daily precipitation
        t_day_start = ee.Date.fromYMD(t.get('year'), t.get('month'), t.get('day'))
        precip_col = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(t_day_start, t_day_start.advance(1, 'day'))
        precip = ee.Image(
            ee.Algorithms.If(
                precip_col.size().gt(0),
                precip_col.first().select('precipitation').rename('precip'),
                ee.Image.constant(-9999).rename('precip')
            )
        )

        # MODIS 8-day Evapotranspiration (MOD16A2)
        et_col = ee.ImageCollection("MODIS/061/MOD16A2").filterDate(t.advance(-16, 'day'), t.advance(1, 'day'))
        et = ee.Image(
            ee.Algorithms.If(
                et_col.size().gt(0),
                et_col.sort('system:time_start', False).first().select('ET').multiply(0.1).rename('modis_et_mm'),
                ee.Image.constant(-9999).rename('modis_et_mm')
            )
        )

        # MODIS 16-day NDVI (MOD13A2)
        ndvi_col = ee.ImageCollection("MODIS/061/MOD13A2").filterDate(t.advance(-30, 'day'), t.advance(1, 'day'))
        ndvi = ee.Image(
            ee.Algorithms.If(
                ndvi_col.size().gt(0),
                ndvi_col.sort('system:time_start', False).first().select('NDVI').multiply(0.0001).rename('ndvi'),
                ee.Image.constant(-9999).rename('ndvi')
            )
        )

        # Stack layers and reduce across the spatial ROI
        stack = ee.Image.cat([temp_c, wind, press, solar, sm, precip, et, ndvi])
        stats = stack.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=5000, maxPixels=1e9)

        return ee.Feature(None, stats).set({
            'datetime': t.format('YYYY-MM-dd HH:mm:ss'),
            'year': t.get('year'),
            'month': t.get('month'),
            'day': t.get('day'),
            'hour': t.get('hour'),
            'region': reg_key,
            'system:time_start': t.millis()
        })

    features_6hourly = ee.FeatureCollection(step_hours.map(extract_time_step))
    task_desc = f'CWF_6Hourly_{reg_key}_{year}'
    file_prefix = f'cwf_6hourly_{reg_key}_{year}'
    task = ee.batch.Export.table.toDrive(
        collection=features_6hourly,
        description=task_desc,
        folder=DATA_EXPORT_FOLDER,
        fileNamePrefix=file_prefix,
        fileFormat='CSV'
    )
    task.start()
    print(f"Dispatched GEE Task for {reg_info['name']} Year {year} (Task ID: {task.id})")
    return task

def download_6hourly_data_locally(year: int, region: str = 'kolhapur', save_dir=None):
    """
    Directly retrieves 6-hourly GEE data into Python memory and saves it as a CSV
    into the local project data directory (bypassing Google Drive export wait times).
    """
    if save_dir is None:
        save_dir = LOCAL_DATA_PATH
    os.makedirs(save_dir, exist_ok=True)

    reg_key, reg_info = get_region_metadata(region)
    roi_coords = reg_info['roi_coords']
    roi = ee.Geometry.Rectangle(roi_coords)

    start_date = ee.Date.fromYMD(year, 1, 1)
    end_date = ee.Date.fromYMD(year + 1, 1, 1)
    total_hours = end_date.difference(start_date, 'hour')
    step_hours = ee.List.sequence(0, total_hours.subtract(1), 6)

    def extract_time_step(h):
        t = start_date.advance(h, 'hour')
        
        era5 = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").filterDate(t, t.advance(1, 'hour')).first()
        temp_c = era5.select('temperature_2m').subtract(273.15).rename('temp_c')
        wind = era5.expression('sqrt(u**2 + v**2)', {
            'u': era5.select('u_component_of_wind_10m'),
            'v': era5.select('v_component_of_wind_10m')
        }).rename('wind_speed')
        press = era5.select('surface_pressure').divide(1000).rename('pressure_kpa')
        solar = era5.select('surface_solar_radiation_downwards').divide(1000000).rename('solar_rad')
        sm = era5.select('volumetric_soil_water_layer_1').rename('soil_moisture')

        t_day_start = ee.Date.fromYMD(t.get('year'), t.get('month'), t.get('day'))
        precip_col = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(t_day_start, t_day_start.advance(1, 'day'))
        precip = ee.Image(ee.Algorithms.If(
            precip_col.size().gt(0),
            precip_col.first().select('precipitation').rename('precip'),
            ee.Image.constant(-9999).rename('precip')
        ))

        et_col = ee.ImageCollection("MODIS/061/MOD16A2").filterDate(t.advance(-16, 'day'), t.advance(1, 'day'))
        et = ee.Image(ee.Algorithms.If(
            et_col.size().gt(0),
            et_col.sort('system:time_start', False).first().select('ET').multiply(0.1).rename('modis_et_mm'),
            ee.Image.constant(-9999).rename('modis_et_mm')
        ))

        ndvi_col = ee.ImageCollection("MODIS/061/MOD13A2").filterDate(t.advance(-30, 'day'), t.advance(1, 'day'))
        ndvi = ee.Image(ee.Algorithms.If(
            ndvi_col.size().gt(0),
            ndvi_col.sort('system:time_start', False).first().select('NDVI').multiply(0.0001).rename('ndvi'),
            ee.Image.constant(-9999).rename('ndvi')
        ))

        stack = ee.Image.cat([temp_c, wind, press, solar, sm, precip, et, ndvi])
        stats = stack.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=5000, maxPixels=1e9)

        return ee.Feature(None, stats).set({
            'datetime': t.format('YYYY-MM-dd HH:mm:ss'),
            'year': t.get('year'),
            'month': t.get('month'),
            'day': t.get('day'),
            'hour': t.get('hour'),
            'region': reg_key,
            'system:time_start': t.millis()
        })

    print(f"[Extractor] Downloading 6-hourly data for {reg_info['name']} ({year}) directly to local storage...")
    features_fc = ee.FeatureCollection(step_hours.map(extract_time_step))
    info = features_fc.getInfo()
    records = [f['properties'] for f in info.get('features', [])]
    
    if not records:
        print(f"[Extractor] Warning: No records returned for region {reg_key}, year {year}.")
        return None

    df = pd.DataFrame(records)
    save_path = os.path.join(save_dir, f'cwf_6hourly_{reg_key}_{year}.csv')
    df.to_csv(save_path, index=False)
    print(f"[Extractor] Saved local CSV: {save_path} ({len(df):,} rows)")
    return save_path

def extract_all_regions(start_year: int = 2020, end_year: int = 2024, download_local: bool = True):
    """
    Extracts 6-hourly meteorological and satellite data for all 4 target regions:
    Kolhapur, Nile Delta, Kansas, and Mekong Delta.
    """
    if not authenticate_gee():
        print("[Extractor] GEE Authentication failed. Cannot proceed with Earth Engine extraction.")
        return []

    results = []
    print(f"[Extractor] Initiating extraction across {len(REGIONS)} regions from {start_year} to {end_year}...")
    for reg_key in REGIONS.keys():
        print(f"\n--- Extracting Region: {REGIONS[reg_key]['name']} ---")
        for yr in range(start_year, end_year + 1):
            if download_local:
                path = download_6hourly_data_locally(year=yr, region=reg_key)
                if path:
                    results.append(path)
            else:
                task = extract_6hourly_data_for_year(year=yr, region=reg_key)
                results.append(task.id)

    if not download_local:
        check_task_status()

    return results

def check_task_status():
    """Lists current status of running/pending Earth Engine export tasks."""
    try:
        tasks = ee.batch.Task.list()
        recent_tasks = tasks[:10]
        print("\n--- Recent GEE Export Tasks ---")
        for t in recent_tasks:
            print(f"ID: {t.id} | Desc: {t.description} | State: {t.state}")
        return recent_tasks
    except Exception as e:
        print(f"Error checking GEE task status: {e}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Region Google Earth Engine (GEE) Climate Extractor")
    parser.add_argument("--region", type=str, default="kolhapur", choices=list(REGIONS.keys()) + ["all"],
                        help="Target agricultural region (kolhapur, nile_delta, kansas, mekong_delta, or all)")
    parser.add_argument("--year", type=int, default=2024, help="Target year for single-year extraction")
    parser.add_argument("--start-year", type=int, default=2020, help="Start year for multi-year extraction")
    parser.add_argument("--end-year", type=int, default=2024, help="End year for multi-year extraction")
    parser.add_argument("--download-local", action="store_true", help="Download CSV directly to local ./data folder")
    parser.add_argument("--all-regions", action="store_true", help="Extract for all 4 global regions")
    parser.add_argument("--check-status", action="store_true", help="Check status of GEE export tasks")

    args = parser.parse_args()

    if args.check_status:
        if authenticate_gee():
            check_task_status()
    elif args.all_regions or args.region == "all":
        extract_all_regions(start_year=args.start_year, end_year=args.end_year, download_local=args.download_local)
    else:
        if authenticate_gee():
            if args.download_local:
                download_6hourly_data_locally(year=args.year, region=args.region)
            else:
                extract_6hourly_data_for_year(year=args.year, region=args.region)
                check_task_status()
