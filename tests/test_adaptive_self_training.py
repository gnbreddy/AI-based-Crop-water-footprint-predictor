import os
import json
import time
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from adaptive_trainer import AdaptiveModelTrainer
from universal_engine import UniversalCropWaterFootprintEngine
from api_gateway import app
from config import LOCAL_DATA_PATH, FINAL_MODEL_PATH

def test_autonomous_self_training_lifecycle():
    print("=" * 85)
    print(" AUTONOMOUS CONTINUAL SELF-TRAINING & UNLOCKED HYPERPARAMETER TEST")
    print("=" * 85)

    trainer = AdaptiveModelTrainer()
    master_df = trainer.load_master_dataset()
    print(f"\n[Step 1] Baseline Master Dataset Loaded: {len(master_df):,} historical rows.")

    # --------------------------------------------------------------------------
    # Step 2: Simulate New Climate Ingestion Batch (e.g. 500 new sensor records)
    # --------------------------------------------------------------------------
    print("\n[Step 2] Simulating New Incoming Stream of 500 Climate Telemetry Observations...")
    sample_records = master_df.sample(500, replace=True).copy()
    # Add minor realistic variance to simulate new climate season
    sample_records['temp_c'] = sample_records['temp_c'] + np.random.normal(0.5, 0.2, len(sample_records))
    sample_records['solar_rad'] = sample_records['solar_rad'] + np.random.normal(0.2, 0.1, len(sample_records))
    sample_records['modis_et_mm'] = sample_records['modis_et_mm'] + np.random.normal(0.05, 0.02, len(sample_records))
    sample_records['year'] = 2026

    # --------------------------------------------------------------------------
    # Step 3: Run Ingestion and Autonomous Retraining with Unlocked Hyperparameters
    # --------------------------------------------------------------------------
    print("\n[Step 3] Executing Autonomous Ingestion & Unlocked Hyperparameter Optimization...")
    retrain_results = trainer.ingest_new_data_and_retrain(
        new_data=sample_records,
        n_iter_search=6, # Fast search for test verification
        cv_folds=3,
        auto_promote=True
    )

    print(f"\n[Step 4] Retraining Evaluation Results:")
    print(f"  -> Global R² Accuracy:       {retrain_results['global_r2']*100:.2f}%")
    print(f"  -> Cross-Validation R²:      {retrain_results['cv_r2']*100:.2f}%")
    print(f"  -> Global RMSE:              {retrain_results['rmse']:.4f} mm")
    print(f"  -> Total Trained Records:    {retrain_results['training_records']:,} rows")
    print(f"  -> Promoted to Production:   {retrain_results['promoted']}")
    print(f"  -> Optimal Hyperparameters Discovered:")
    for k, v in retrain_results['optimal_hyperparameters'].items():
        print(f"     • {k}: {v}")

    assert retrain_results['status'] == 'success'
    assert retrain_results['promoted'] is True
    assert retrain_results['global_r2'] >= 0.90

    # --------------------------------------------------------------------------
    # Step 5: Verify Live Model Hot-Reloading in Universal Engine
    # --------------------------------------------------------------------------
    print("\n[Step 5] Testing Hot-Reloading in Live Universal Prediction Engine...")
    engine = UniversalCropWaterFootprintEngine()
    reloaded = engine.reload_model()
    assert reloaded is True, "Engine failed to hot-reload newly trained model!"
    
    # Test a prediction with hot-reloaded weights
    pred_res = engine.analyze_location(
        temp_c=31.5,
        solar_rad_mj=22.0,
        precip_mm=4.0,
        soil_moisture=0.25,
        rh_pct=55.0,
        wind_speed_ms=2.5,
        crop_type='sugarcane',
        soil_type='clay_loam'
    )
    print(f"  -> [PASS] Live Prediction Successful with Self-Trained Model:")
    print(f"     Actual ET: {pred_res['evapotranspiration_depth_mm']['actual_et_mm']} mm | Total CWF: {pred_res['crop_water_footprint_m3_ton']['total_water_footprint_m3_ton']} m³/t")

    # --------------------------------------------------------------------------
    # Step 6: Test FastAPI Self-Training & Status Endpoints
    # --------------------------------------------------------------------------
    print("\n[Step 6] Testing FastAPI Autonomous Retraining Endpoints...")
    client = TestClient(app)
    
    status_resp = client.get("/api/v1/model/status")
    print(f"  -> GET /api/v1/model/status: {status_resp.status_code}")
    model_status = status_resp.json()
    print(f"     Status: {model_status.get('status', 'active')} | R²: {model_status.get('global_r2_accuracy', 'N/A')}")
    assert status_resp.status_code == 200

    print("\n" + "=" * 85)
    print(" AUTONOMOUS CONTINUAL SELF-TRAINING & UNLOCKED HYPERPARAMETERS VERIFIED (PASS)")
    print("=" * 85)

if __name__ == "__main__":
    test_autonomous_self_training_lifecycle()
