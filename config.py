import os

# ==============================================================================
# Google Earth Engine (GEE) Configuration
# ==============================================================================
# Protected via environment variable (set GEE_PROJECT_ID in your .env or shell)
GEE_PROJECT_ID = os.getenv('GEE_PROJECT_ID', 'gen-lang-client-0784106715')
ROI_COORDS = [73.40, 15.42, 74.42, 17.17]  # [min_lon, min_lat, max_lon, max_lat] default Kolhapur

# Multi-Region Agro-Ecological Configurations for GEE & ML Ingestion
REGIONS = {
    'kolhapur': {
        'name': 'Kolhapur Sugarcane (India)',
        'crop': 'sugarcane',
        'soil': 'clay_loam',
        'roi_coords': [73.40, 15.42, 74.42, 17.17],
        'center': [16.70, 74.24],
        'elevation_m': 570.0,
        'kc': 0.50,
        'yield_baseline': 150.0,
        'growing_season_days': 360,
        'description': 'Tropical wet-and-dry monsoon sugarcane heartland of Western India.'
    },
    'nile_delta': {
        'name': 'Nile Delta Cotton (Egypt)',
        'crop': 'cotton',
        'soil': 'sandy_loam',
        'roi_coords': [30.40, 30.50, 31.60, 31.50],
        'center': [31.00, 31.00],
        'elevation_m': 15.0,
        'kc': 0.85,
        'yield_baseline': 3.5,
        'growing_season_days': 180,
        'description': 'Hyper-arid Mediterranean delta intensive irrigation cotton belt.'
    },
    'kansas': {
        'name': 'Kansas Wheat (USA)',
        'crop': 'wheat',
        'soil': 'silt_loam',
        'roi_coords': [-99.50, 37.80, -98.00, 39.00],
        'center': [38.50, -98.50],
        'elevation_m': 500.0,
        'kc': 0.90,
        'yield_baseline': 5.0,
        'growing_season_days': 220,
        'description': 'North American Great Plains temperate winter wheat grain belt.'
    },
    'mekong_delta': {
        'name': 'Mekong Monsoon Rice (Vietnam)',
        'crop': 'rice',
        'soil': 'clay',
        'roi_coords': [105.00, 9.80, 106.20, 10.80],
        'center': [10.20, 105.80],
        'elevation_m': 10.0,
        'kc': 1.15,
        'yield_baseline': 4.5,
        'growing_season_days': 120,
        'description': 'Tropical monsoon alluvial floodplain high-intensity paddy rice system.'
    }
}

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
# Unlocked Adaptive LightGBM Hyperparameters & Dynamic Search Distributions
# ==============================================================================
DEFAULT_LGBM_PARAMS = {
    'learning_rate': 0.035,
    'n_estimators': 300,
    'num_leaves': 31,
    'max_depth': 6,
    'subsample': 0.85,
    'colsample_bytree': 0.85,
    'reg_alpha': 0.10,
    'reg_lambda': 0.20,
    'min_child_samples': 20,
    'random_state': 42,
    'verbose': -1,
    'n_jobs': -1
}

# Unlocked full parameter search space for dynamic auto-tuning when new data arrives
UNLOCKED_PARAM_DISTRIBUTIONS = {
    'lgbm__learning_rate': [0.01, 0.02, 0.035, 0.05, 0.08],
    'lgbm__n_estimators': [150, 300, 450, 600],
    'lgbm__num_leaves': [15, 31, 63, 127],
    'lgbm__max_depth': [-1, 4, 6, 8, 10],
    'lgbm__subsample': [0.70, 0.85, 0.95, 1.0],
    'lgbm__colsample_bytree': [0.70, 0.80, 0.90, 1.0],
    'lgbm__reg_alpha': [0.001, 0.01, 0.1, 0.5, 1.0],
    'lgbm__reg_lambda': [0.001, 0.01, 0.1, 0.5, 1.0],
    'lgbm__min_child_samples': [10, 20, 30, 50]
}

# Fast adaptive grid for lightweight online retraining on new data batches
FAST_PARAM_GRID = {
    'lgbm__learning_rate': [0.02, 0.035, 0.05],
    'lgbm__n_estimators': [200, 350, 500],
    'lgbm__num_leaves': [31, 63],
    'lgbm__subsample': [0.85, 0.95],
    'lgbm__colsample_bytree': [0.85, 1.0],
    'lgbm__reg_alpha': [0.01, 0.1],
    'lgbm__reg_lambda': [0.01, 0.1]
}

MAX_ACCURACY_PARAM_GRID = UNLOCKED_PARAM_DISTRIBUTIONS
PARAM_GRID = FAST_PARAM_GRID
OPTIMAL_LGBM_PARAMS = DEFAULT_LGBM_PARAMS

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
