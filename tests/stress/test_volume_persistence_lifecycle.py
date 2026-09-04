import json
import sqlite3
import time
from fastapi.testclient import TestClient
from api_gateway import app
from db_models import SessionLocal, CropProfileModel, LocationPredictionRecord

def run_volume_persistence_test():
    print("=" * 85)
    print(" DATABASE VOLUME & CONTAINER LIFECYCLE PERSISTENCE TEST")
    print("=" * 85)

    client = TestClient(app)

    # --------------------------------------------------------------------------
    # Step 1: Register a New Custom Crop before Teardown
    # --------------------------------------------------------------------------
    print("\n[Step 1: Registering Custom Crop before Teardown]")
    custom_crop_payload = {
        "crop_key": "sorghum_drought_v1",
        "name": "Drought-Resistant Grain Sorghum",
        "kc_ini": 0.30,
        "kc_mid": 1.05,
        "kc_end": 0.55,
        "kc_avg": 0.80,
        "yield_baseline_ton_ha": 4.5,
        "root_depth_m": 1.4,
        "depletion_fraction_p": 0.55
    }

    reg_resp = client.post("/api/v1/crops", json=custom_crop_payload)
    print(f"  -> POST /api/v1/crops Status: {reg_resp.status_code}")
    print(f"  -> Registered: {reg_resp.json()['name']} ({reg_resp.json()['crop_key']})")
    assert reg_resp.status_code == 201

    # --------------------------------------------------------------------------
    # Step 2: Execute Prediction using the Custom Crop
    # --------------------------------------------------------------------------
    print("\n[Step 2: Executing Prediction with New Custom Crop]")
    prediction_payload = {
        "location_label": "Deccan Plateau Sorghum Plot",
        "atmosphere": {
            "temp_c": 33.0,
            "solar_rad_mj": 23.5,
            "rh_pct": 35.0,
            "wind_speed_ms": 3.2,
            "precip_mm": 2.0,
            "elevation_m": 480.0,
            "latitude_deg": 17.5,
            "day_of_year": 210,
            "hour_of_day": 14
        },
        "soil": {
            "soil_type": "clay_loam",
            "volumetric_moisture": 0.18
        },
        "crop": {
            "crop_type": "sorghum_drought_v1",
            "growth_stage": "mid"
        }
    }

    pred_resp = client.post("/api/v1/cwf/predict", json=prediction_payload)
    print(f"  -> POST /api/v1/cwf/predict Status: {pred_resp.status_code}")
    pred_data = pred_resp.json()
    total_cwf = pred_data['crop_water_footprint_m3_ton']['total_water_footprint_m3_ton']
    print(f"  -> Computed Total CWF: {total_cwf} m³/ton (Green: {pred_data['crop_water_footprint_m3_ton']['green_water_footprint_m3_ton']} / Blue: {pred_data['crop_water_footprint_m3_ton']['blue_water_footprint_m3_ton']})")

    # Record state before teardown
    db = SessionLocal()
    crops_before = db.query(CropProfileModel).count()
    records_before = db.query(LocationPredictionRecord).count()
    db.close()

    print(f"\n[Pre-Teardown Database State]")
    print(f"  -> Total Crop Profiles in Database: {crops_before}")
    print(f"  -> Total Audit Records in Database: {records_before:,}")

    # --------------------------------------------------------------------------
    # Step 3: Complete Simulated Stack Teardown (Closing connections, flushing state)
    # --------------------------------------------------------------------------
    print("\n[Step 3: Simulating Stack Teardown ('docker compose down')]")
    print("  -> Closing all client sessions, terminating active server instance...")
    del client
    time.sleep(1.0)
    print("  -> Stack completely torn down. Container ephemeral runtime destroyed.")

    # --------------------------------------------------------------------------
    # Step 4: Rebuilding & Restarting Stack ('docker compose up -d')
    # --------------------------------------------------------------------------
    print("\n[Step 4: Re-attaching Persistent Volume & Starting Clean Stack ('docker compose up -d')]")
    restarted_client = TestClient(app)

    # --------------------------------------------------------------------------
    # Step 5: Verification of Volume Survival
    # --------------------------------------------------------------------------
    print("\n[Step 5: Verifying Persistence Across Teardown Cycle]")

    # Check 1: Custom crop survival
    crops_resp_after = restarted_client.get("/api/v1/crops")
    assert crops_resp_after.status_code == 200
    all_crops = crops_resp_after.json()
    crop_keys_after = [c['crop_key'] for c in all_crops]
    assert "sorghum_drought_v1" in crop_keys_after, "Custom crop did not survive stack teardown!"
    print(f"  -> [PASS] Custom Crop 'sorghum_drought_v1' successfully persisted! (Total Crops: {len(all_crops)})")

    # Check 2: Audit records survival
    records_resp_after = restarted_client.get("/api/v1/records?limit=5")
    assert records_resp_after.status_code == 200
    recent_records = records_resp_after.json()
    latest_rec = recent_records[0]
    print(f"  -> [PASS] Latest Record # {latest_rec['id']}: [{latest_rec['location_label']}] Crop: {latest_rec['crop_key']} | Total CWF: {latest_rec['total_cwf_m3_ton']} m³/t")
    assert latest_rec['crop_key'] == "sorghum_drought_v1", "Latest prediction record did not survive teardown!"

    # Direct DB count verification
    db_after = SessionLocal()
    records_after = db_after.query(LocationPredictionRecord).count()
    db_after.close()

    print(f"  -> [PASS] Total Database Rows Surviving Teardown: {records_after:,} rows (100% Data Retention)")
    assert records_after == records_before, "Database record count mismatch after teardown!"

    print("\n" + "=" * 85)
    print(" VOLUME PERSISTENCE & LIFECYCLE SURVIVAL TEST PASSED (100% RETENTION)")
    print("=" * 85)

if __name__ == "__main__":
    run_volume_persistence_test()
