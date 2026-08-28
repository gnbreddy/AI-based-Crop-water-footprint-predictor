import os
import shutil
import pytest
import pandas as pd
import numpy as np

from config import LOCAL_DATA_PATH, OUTPUT_DIR, FEATURES, TARGET, BASE_FEATURES, LAG_FEATURES
from mock_data_generator import generate_mock_data
from compiler import compile_datasets
from trainer import train_and_evaluate, train_final_production_model
from calibrator import CropWaterFootprintCalibrator
from visualizer import (
    plot_feature_importance,
    plot_water_footprint_breakdown,
    plot_learning_curve,
    generate_footprint_map
)

TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data_tmp')
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_output_tmp')

@pytest.fixture(scope="session", autouse=True)
def setup_teardown_test_env():
    """Sets up temporary test data and teardowns after test session."""
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    
    # Generate 3 years of mock data for testing
    generate_mock_data(start_year=2021, end_year=2023, data_dir=TEST_DATA_DIR)
    
    yield
    
    # Cleanup temporary test folders
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)

def test_compiler():
    """Test if compiler merges CSVs, creates lag features, and preserves chronological order."""
    df = compile_datasets(data_dir=TEST_DATA_DIR)
    assert df is not None, "Compiler returned None."
    assert not df.empty, "Compiled DataFrame is empty."
    assert 'year' in df.columns, "Missing 'year' column for validation split."
    assert len(df['year'].unique()) == 3, f"Expected 3 years, found {len(df['year'].unique())}."
    
    # Check that all features (including lag features) and target are present
    for feat in FEATURES:
        assert feat in df.columns, f"Engineered feature '{feat}' missing from compiled DataFrame."
    assert TARGET in df.columns, f"Target '{TARGET}' missing from compiled DataFrame."

    assert df[FEATURES + [TARGET]].isna().sum().sum() == 0, "Compiled dataset contains unhandled NaN values."
    
    # Verify master engineered dataset was saved to test data dir
    assert os.path.exists(os.path.join(TEST_DATA_DIR, "master_engineered_dataset.csv")), "master_engineered_dataset.csv was not saved."

def test_trainer_execution():
    """Test if the LightGBM expanding-window training executes and returns valid metrics."""
    df = compile_datasets(data_dir=TEST_DATA_DIR)
    
    fast_param_grid = {
        'lgbm__learning_rate': [0.05],
        'lgbm__n_estimators': [50],
        'lgbm__num_leaves': [20]
    }
    
    best_run = train_and_evaluate(df, param_grid=fast_param_grid, data_dir=TEST_DATA_DIR)
    
    assert best_run is not None, "Trainer did not return a result."
    assert 'r2_accuracy' in best_run, "Missing accuracy metric in results."
    assert 'weight_adjustments' in best_run, "Missing feature weight adjustments."
    assert len(best_run['weight_adjustments']) == len(FEATURES), "Feature weight count mismatch."
    assert 'model' in best_run, "Model object not returned in results."
    assert best_run['predicted_year'] > 2021, "Validation window did not step forward."
    assert 'rmse' in best_run and 'mae' in best_run, "Missing RMSE or MAE in metrics."

    # Verify epoch CSV artifacts were saved
    assert os.path.exists(os.path.join(TEST_DATA_DIR, "epoch_validation_history.csv")), "epoch_validation_history.csv missing."
    assert os.path.exists(os.path.join(TEST_DATA_DIR, "epoch_feature_weights.csv")), "epoch_feature_weights.csv missing."
    assert os.path.exists(os.path.join(TEST_DATA_DIR, f"epoch_predictions_{best_run['predicted_year']}.csv")), "Epoch prediction CSV missing."

    # Test final locked production model training
    prod_run = train_final_production_model(df, data_dir=TEST_DATA_DIR)
    assert prod_run is not None, "Production model fit failed."
    assert prod_run['global_r2_accuracy'] > 0.90, "Production model accuracy is below threshold."
    assert os.path.exists(os.path.join(TEST_DATA_DIR, "final_locked_feature_weights.csv")), "final_locked_feature_weights.csv missing."

def test_calibrator_computation_and_optimization():
    """Test CWF calculation formulas and parameter calibration optimization."""
    df = compile_datasets(data_dir=TEST_DATA_DIR)
    calibrator = CropWaterFootprintCalibrator()

    et_series = df[TARGET].values[:100]
    precip_series = df['precip'].values[:100]

    # 1. Forward calculation
    res = calibrator.compute_footprint(et_series, precip_series)
    assert res['total_water_footprint_m3_ton'] > 0, "Total water footprint should be positive."
    assert res['green_water_footprint_m3_ton'] >= 0, "Green water footprint should be non-negative."
    assert res['blue_water_footprint_m3_ton'] >= 0, "Blue water footprint should be non-negative."
    assert np.isclose(res['total_water_footprint_m3_ton'], res['green_water_footprint_m3_ton'] + res['blue_water_footprint_m3_ton']), "TWF must equal GWF + BWF."

    # 2. Coefficient calibration optimization
    target_twf = 120.0 # m3/ton benchmark
    calib_res = calibrator.calibrate_coefficients(et_series, precip_series, target_twf=target_twf, target_gwf_ratio=0.75)
    assert calib_res['optimization_success'], "Calibration optimizer failed to converge."
    opt_params = calib_res['optimized_params']
    assert 0.5 <= opt_params['crop_coefficient_kc'] <= 1.6, "Optimized Kc out of physical bounds."
    assert 0.4 <= opt_params['effective_precip_factor'] <= 0.95, "Optimized alpha out of physical bounds."

def test_visualizer_outputs():
    """Test visualizer plot generation and interactive map export."""
    df = compile_datasets(data_dir=TEST_DATA_DIR)
    calibrator = CropWaterFootprintCalibrator()
    cwf_res = calibrator.compute_footprint(df[TARGET].values[:100], df['precip'].values[:100])

    mock_run = {
        'predicted_year': 2023,
        'r2_accuracy': 0.88,
        'weight_adjustments': {feat: np.random.uniform(10, 100) for feat in FEATURES}
    }

    feat_img = os.path.join(TEST_OUTPUT_DIR, 'test_feature_importance.png')
    plot_feature_importance(mock_run, save_path=feat_img)
    assert os.path.exists(feat_img), "Feature importance chart file was not created."

    curve_img = os.path.join(TEST_OUTPUT_DIR, 'test_learning_curve.png')
    mock_history = [
        {'predicted_year': 2021, 'r2_accuracy': 0.85, 'rmse': 0.35, 'mae': 0.25},
        {'predicted_year': 2022, 'r2_accuracy': 0.88, 'rmse': 0.31, 'mae': 0.22},
        {'predicted_year': 2023, 'r2_accuracy': 0.91, 'rmse': 0.28, 'mae': 0.19}
    ]
    plot_learning_curve(mock_history, save_path=curve_img)
    assert os.path.exists(curve_img), "Learning curve chart file was not created."

    cwf_img = os.path.join(TEST_OUTPUT_DIR, 'test_cwf_breakdown.png')
    plot_water_footprint_breakdown(cwf_res, save_path=cwf_img)
    assert os.path.exists(cwf_img), "CWF breakdown chart file was not created."

    map_html = os.path.join(TEST_OUTPUT_DIR, 'test_map.html')
    generate_footprint_map(2023, save_path=map_html)
    assert os.path.exists(map_html), "Interactive map HTML was not created."

def test_universal_engine():
    """Test location-agnostic universal CWF engine across global climate regimes."""
    from universal_engine import UniversalCropWaterFootprintEngine
    from schemas import UniversalIngestionRequest, AtmosphericPayload, SoilPayload, CropPayload
    from normalization_engine import PhysicalNormalizationEngine
    from crop_repository import CropSoilRepository

    # 1. Test Physical Normalization Engine
    norm = PhysicalNormalizationEngine()
    vpd = norm.vapor_pressure_deficit(temp_c=30.0, rh_pct=40.0)
    assert vpd > 0.0, "VPD should be positive for RH < 100%."
    
    ssi = norm.soil_water_stress_index(volumetric_moisture=0.20, field_capacity=0.30, wilting_point=0.10)
    assert np.isclose(ssi, 0.50), f"Expected SSI = 0.50, got {ssi}"

    r_a = norm.extraterrestrial_radiation(latitude_deg=20.0, day_of_year=172)
    assert r_a > 10.0, "Extraterrestrial radiation out of expected physical bounds."

    # 2. Test Dynamic Crop & Soil Repository
    repo = CropSoilRepository()
    wheat_prof = repo.get_crop_profile('wheat', growth_stage='mid')
    assert wheat_prof['kc_selected'] == 1.15, "Wheat mid-season Kc mismatch."
    assert wheat_prof['yield_baseline_ton_ha'] > 0, "Yield baseline must be positive."

    # Test dynamic custom crop registration
    reg_success = repo.register_custom_crop(
        crop_key='quinoa', name='Highland Quinoa',
        kc_ini=0.30, kc_mid=1.00, kc_end=0.45, kc_avg=0.75,
        yield_baseline_ton_ha=2.5, root_depth_m=0.8
    )
    assert reg_success, "Failed to dynamically register custom crop."
    quinoa_prof = repo.get_crop_profile('quinoa')
    assert quinoa_prof['name'] == 'Highland Quinoa'

    # 3. Test Universal Ingestion Pipeline via Pydantic Payload
    engine = UniversalCropWaterFootprintEngine()
    sample_request = UniversalIngestionRequest(
        location_label="Nile Delta, Egypt",
        atmosphere=AtmosphericPayload(
            temp_c=36.0, solar_rad_mj=25.0, rh_pct=30.0,
            wind_speed_ms=4.0, precip_mm=0.0, elevation_m=15.0, latitude_deg=30.5
        ),
        soil=SoilPayload(soil_type='sandy_loam', volumetric_moisture=0.12),
        crop=CropPayload(crop_type='cotton', growth_stage='mid')
    )
    resp = engine.process_payload(sample_request)
    assert resp.status == "success", "Universal payload processing failed."
    assert resp.crop_water_footprint_m3_ton.total_water_footprint_m3_ton > 0
    assert resp.crop_water_footprint_m3_ton.blue_water_footprint_m3_ton > 0
    assert resp.thermodynamic_diagnostics.vapor_pressure_deficit_kpa > 0

def test_fastapi_gateway():
    """Test FastAPI Gateway endpoints, validation, session injection, and audit logging."""
    from fastapi.testclient import TestClient
    from api_gateway import app

    client = TestClient(app)

    # 1. Health check endpoint
    h_resp = client.get("/health")
    assert h_resp.status_code == 200
    assert h_resp.json()["status"] == "healthy"
    assert h_resp.json()["database"] == "connected"

    # 2. List crops and soils
    c_resp = client.get("/api/v1/crops")
    assert c_resp.status_code == 200
    assert len(c_resp.json()) > 0

    s_resp = client.get("/api/v1/soils")
    assert s_resp.status_code == 200
    assert len(s_resp.json()) > 0

    # 3. Predict CWF via POST /api/v1/cwf/predict
    payload = {
        "location_label": "Imperial Valley, California",
        "atmosphere": {
            "temp_c": 38.0,
            "solar_rad_mj": 26.5,
            "rh_pct": 20.0,
            "wind_speed_ms": 4.2,
            "precip_mm": 0.0,
            "elevation_m": -15.0,
            "latitude_deg": 32.8,
            "day_of_year": 190,
            "hour_of_day": 13
        },
        "soil": {
            "soil_type": "sandy_loam",
            "volumetric_moisture": 0.10
        },
        "crop": {
            "crop_type": "cotton",
            "growth_stage": "mid"
        }
    }

    pred_resp = client.post("/api/v1/cwf/predict", json=payload)
    assert pred_resp.status_code == 200
    data = pred_resp.json()
    assert data["status"] == "success"
    assert data["location_label"] == "Imperial Valley, California"
    assert data["crop_water_footprint_m3_ton"]["total_water_footprint_m3_ton"] > 0
    assert data["crop_water_footprint_m3_ton"]["blue_water_footprint_m3_ton"] > 0

    # 4. Check audit log in database via GET /api/v1/records
    rec_resp = client.get("/api/v1/records?limit=5")
    assert rec_resp.status_code == 200
    assert len(rec_resp.json()) > 0
    assert rec_resp.json()[0]["crop_key"] == "cotton"

def test_streaming_pipeline():
    """Test asynchronous high-throughput telemetry ingestion and batch processing."""
    import asyncio
    from streaming_pipeline import run_streaming_benchmark

    res = asyncio.run(run_streaming_benchmark(num_records=50, batch_size=25))
    assert res['total_records'] == 50
    assert res['throughput_records_per_sec'] > 0

def test_adaptive_self_training_and_hot_reloading():
    """Test dynamic hyperparameter optimization, model promotion, and hot-reloading."""
    from adaptive_trainer import AdaptiveModelTrainer
    from universal_engine import UniversalCropWaterFootprintEngine

    trainer = AdaptiveModelTrainer()
    df = trainer.load_master_dataset().sample(200, random_state=42)
    res = trainer.optimize_and_train(dataset=df, n_iter_search=2, cv_folds=2, auto_promote=False)
    
    assert res['status'] == 'success'
    assert 'learning_rate' in res['optimal_hyperparameters']
    assert res['global_r2'] > 0.80

    engine = UniversalCropWaterFootprintEngine()
    assert engine.reload_model() is True
