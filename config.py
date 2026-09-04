import os

# Try loading .env file if present
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_path):
    try:
        with open(_env_path, 'r') as _ef:
            for _line in _ef:
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _v = _line.split('=', 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
    except Exception:
        pass

# ==============================================================================
# Google Earth Engine (GEE) Configuration
# ==============================================================================
# Protected via environment variable (set GEE_PROJECT_ID in your .env or shell)
GEE_PROJECT_ID = os.getenv('GEE_PROJECT_ID', 'gen-lang-client-0784106715')
ROI_COORDS = [73.40, 15.42, 74.42, 17.17]  # [min_lon, min_lat, max_lon, max_lat] default Kolhapur

# Gemini AI API Key for Dynamic Agro-Hydrological Anatomy & Synthesis
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Multi-Region Agro-Ecological Configurations for GEE & ML Ingestion
REGIONS = {
    'kolhapur': {
        'name': 'Kolhapur District Basin (India)',
        'crop': 'sugarcane',
        'soil': 'clay_loam',
        'roi_coords': [73.40, 15.42, 74.42, 17.17],
        'center': [16.70, 74.24],
        'elevation_m': 570.0,
        'kc': 0.50,
        'yield_baseline': 105.0,
        'growing_season_days': 360,
        'description': 'Tropical wet-and-dry monsoon agro-basin of Western India.'
    },
    'karveer': {
        'name': 'Karveer Taluka (Central Panchganga Basin)',
        'crop': 'sugarcane',
        'soil': 'clay_loam',
        'roi_coords': [74.15, 16.60, 74.35, 16.80],
        'center': [16.7050, 74.2433],
        'elevation_m': 565.0,
        'kc': 0.50,
        'yield_baseline': 105.0,
        'growing_season_days': 360,
        'description': 'Central riverine plain with intensive canal and lift irrigation.'
    },
    'shirol': {
        'name': 'Shirol Taluka (Panchganga-Krishna Confluence)',
        'crop': 'sugarcane',
        'soil': 'alluvial_clay',
        'roi_coords': [74.50, 16.60, 74.70, 16.80],
        'center': [16.6917, 74.5833],
        'elevation_m': 540.0,
        'kc': 0.50,
        'yield_baseline': 115.0,
        'growing_season_days': 360,
        'description': 'High water table alluvial floodplain with deep capillary upflux.'
    },
    'radhanagari': {
        'name': 'Radhanagari Taluka (Western Ghats Catchment)',
        'crop': 'rice',
        'soil': 'lateritic_loam',
        'roi_coords': [73.85, 16.30, 74.10, 16.55],
        'center': [16.4167, 73.9833],
        'elevation_m': 620.0,
        'kc': 1.05,
        'yield_baseline': 4.5,
        'growing_season_days': 120,
        'description': 'High-rainfall Western Ghats forest catchment zone.'
    },
    'kagal': {
        'name': 'Kagal Taluka (Southern Agro-Corridor)',
        'crop': 'sugarcane',
        'soil': 'black_clay',
        'roi_coords': [74.20, 16.50, 74.40, 16.68],
        'center': [16.5833, 74.3167],
        'elevation_m': 575.0,
        'kc': 0.50,
        'yield_baseline': 100.0,
        'growing_season_days': 360,
        'description': 'Heavy Vertisol clay soil agro-corridor.'
    },
    'hatkanangale': {
        'name': 'Hatkanangale Taluka (Northern Belt)',
        'crop': 'cotton',
        'soil': 'black_clay_loam',
        'roi_coords': [74.35, 16.65, 74.55, 16.85],
        'center': [16.7417, 74.4444],
        'elevation_m': 550.0,
        'kc': 0.85,
        'yield_baseline': 3.5,
        'growing_season_days': 180,
        'description': 'Northern cash crop and sugarcane processing belt.'
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

# Advanced Biophysical & Plant Physiology Features (FAO-56 Dual Kc, GDD, Stomatal Resistance)
BIOPHYSICAL_FEATURES = [
    'gdd_cum',               # Cumulative Growing Degree Days (°C-days)
    'dynamic_root_depth',    # Effective root zone depth Zr(t) in meters (0.2m - 1.2m)
    'kcb',                   # Basal crop coefficient (transpiration, coupled to NDVI)
    'ke',                    # Soil surface evaporation coefficient (rapid decay)
    'kc_dual',               # Combined dual crop coefficient (Kcb + Ke)
    'f_vpd_attenuation',     # Jarvis-Stewart stomatal closure attenuation factor [0.2 - 1.0]
    'flash_drought_idx',     # Atmospheric thirst vs root moisture ratio (VPD / SM_root)
    'flood_saturation_idx'   # Waterlogging and root asphyxiation index
]

# Extended feature set incorporating biophysical plant physiology
EXTENDED_FEATURES = FEATURES + BIOPHYSICAL_FEATURES

# Target variable (Evapotranspiration in mm from MODIS MOD16A2 / ground truth)
TARGET = 'modis_et_mm'

# Dataset regimes are provenance/quality labels, not causal claims.  The
# chronological audit found a large target-distribution shift starting in 2020;
# training and reports can use these labels to keep diagnostics transparent.
DATASET_REGIMES = {
    'observed_target_regime_pre_2020': range(2000, 2020),
    'observed_target_transition_2020': range(2020, 2021),
    'observed_target_regime_post_2020': range(2021, 2026),
}

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
