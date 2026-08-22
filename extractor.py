import ee
from config import GEE_PROJECT_ID, ROI_COORDS, DATA_EXPORT_FOLDER

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

def extract_6hourly_data_for_year(year):
    """
    Extracts 6-hourly aggregated meteorological and remote sensing features for a given year
    over the Region of Interest (ROI) and submits an Earth Engine batch export task to Google Drive.
    """
    roi = ee.Geometry.Rectangle(ROI_COORDS)
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
            'system:time_start': t.millis()
        })

    features_6hourly = ee.FeatureCollection(step_hours.map(extract_time_step))
    task = ee.batch.Export.table.toDrive(
        collection=features_6hourly,
        description=f'CWF_6Hourly_Export_{year}',
        folder=DATA_EXPORT_FOLDER,
        fileNamePrefix=f'cwf_6hourly_{year}',
        fileFormat='CSV'
    )
    task.start()
    print(f"Dispatched 6-Hourly Data Task for Year: {year} (Task ID: {task.id})")
    return task

def download_6hourly_data_locally(year, save_dir=None):
    """
    Directly retrieves 6-hourly GEE data into Python memory and saves it as a CSV
    into the local project data directory (bypassing Google Drive export wait times).
    """
    import os
    import pandas as pd
    from config import LOCAL_DATA_PATH

    if save_dir is None:
        save_dir = LOCAL_DATA_PATH
    os.makedirs(save_dir, exist_ok=True)

    roi = ee.Geometry.Rectangle(ROI_COORDS)
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
            'system:time_start': t.millis()
        })

    print(f"[Extractor] Downloading 6-hourly data for {year} directly to local storage...")
    features_fc = ee.FeatureCollection(step_hours.map(extract_time_step))
    info = features_fc.getInfo()
    records = [f['properties'] for f in info.get('features', [])]
    
    if not records:
        print(f"[Extractor] Warning: No records returned for year {year}.")
        return None

    df = pd.DataFrame(records)
    save_path = os.path.join(save_dir, f'cwf_6hourly_{year}.csv')
    df.to_csv(save_path, index=False)
    print(f"[Extractor] Saved local CSV: {save_path} ({len(df):,} rows)")
    return save_path

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
