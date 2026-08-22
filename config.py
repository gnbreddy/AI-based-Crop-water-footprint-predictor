import os

# ==============================================================================
# Google Earth Engine (GEE) Configuration
# ==============================================================================
# Protected via environment variable (set GEE_PROJECT_ID in your .env or shell)
GEE_PROJECT_ID = os.getenv('GEE_PROJECT_ID', 'gen-lang-client-0784106715')
ROI_COORDS = [73.40, 15.42, 74.42, 17.17]  # [min_lon, min_lat, max_lon, max_lat]

# ==============================================================================
# File System & Storage Paths
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_EXPORT_FOLDER = 'GEE_CWF_6Hourly_Data'
LOCAL_DATA_PATH = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
MODEL_SAVE_PATH = os.path.join(OUTPUT_DIR, 'best_lgbm_model.pkl')

os.makedirs(LOCAL_DATA_PATH, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================================================================
# Visualization & Spatial Heatmap Configuration
# ==============================================================================
HEATMAP_TARGET_YEAR = 2025
MAP_INITIAL_LOCATION = [16.7, 74.2]
MAP_INITIAL_ZOOM = 9

# ==============================================================================
# Feature Engineering & Target Variables
# ==============================================================================
# Base raw features extracted from GEE collections (ERA5-Land, CHIRPS, MODIS)
BASE_FEATURES = [
    'temp_c',
    'wind_speed',
    'pressure_kpa',
    'solar_rad',
    'precip',
    'soil_moisture',
    'ndvi'
]

# Engineered temporal lag features (6h, 12h, 24h prior timesteps)
LAG_FEATURES = [
    'temp_c_lag1',
    'precip_lag1',
    'ndvi_lag1',
    'soil_moisture_lag1',
    'temp_c_lag4',
    'soil_moisture_lag4'
]

# Rolling window aggregated statistics (24h rolling averages & cumulative sums)
ROLLING_FEATURES = [
    'temp_c_roll24h',
    'solar_rad_roll24h',
    'soil_moisture_roll24h',
    'precip_cum48h'
]

# Cyclical temporal harmonics (capturing diurnal and seasonal solar zenith angles)
CYCLICAL_FEATURES = [
    'sin_hour',
    'cos_hour',
    'sin_doy',
    'cos_doy'
]

# Full feature set used by LightGBM model
FEATURES = BASE_FEATURES + LAG_FEATURES + ROLLING_FEATURES + CYCLICAL_FEATURES

# Target variable (Evapotranspiration in mm from MODIS MOD16A2 / ground truth)
TARGET = 'modis_et_mm'

# ==============================================================================
# Final Locked-in Optimal LightGBM Hyperparameters
# (Derived from 25-Epoch Cyclic Expanding Window Empirical Observations)
# ==============================================================================
OPTIMAL_LGBM_PARAMS = {
    'learning_rate': 0.02,
    'n_estimators': 400,
    'num_leaves': 63,
    'subsample': 0.95,
    'colsample_bytree': 0.85,
    'reg_alpha': 0.10,
    'reg_lambda': 0.10,
    'min_child_samples': 20,
    'random_state': 42,
    'verbose': -1,
    'n_jobs': -1
}

PARAM_GRID = {
    'lgbm__learning_rate': [0.02],
    'lgbm__n_estimators': [400],
    'lgbm__num_leaves': [63],
    'lgbm__subsample': [0.95],
    'lgbm__colsample_bytree': [0.85],
    'lgbm__reg_alpha': [0.10],
    'lgbm__reg_lambda': [0.10]
}

FAST_PARAM_GRID = PARAM_GRID
MAX_ACCURACY_PARAM_GRID = PARAM_GRID

# ==============================================================================
# Locked-in Crop Water Footprint (CWF) Empirical & Physical Constants
# ==============================================================================
DEFAULT_CWF_PARAMS = {
    'crop_coefficient_kc': 0.50,       # Globally optimized Kc factor
    'effective_precip_factor': 0.95,   # Globally optimized effective rainfall factor (alpha)
    'yield_baseline': 150.0,           # Baseline regional crop yield (ton/ha)
    'water_conversion_factor': 10.0    # 1 mm depth over 1 ha = 10 m^3/ha
}
HEATMAP_YIELD_BASELINE = DEFAULT_CWF_PARAMS['yield_baseline']
FINAL_MODEL_PATH = os.path.join(OUTPUT_DIR, 'final_production_model.pkl')
