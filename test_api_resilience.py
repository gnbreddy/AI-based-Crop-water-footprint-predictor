import json
from fastapi.testclient import TestClient
from api_gateway import app

def run_resilience_stress_tests():
    print("=" * 80)
    print(" FASTAPI & PYDANTIC VALIDATION RESILIENCE STRESS-TEST")
    print("=" * 80)

    client = TestClient(app)

    # --------------------------------------------------------------------------
    # Check 1: Startup Model Loading & System Health
    # --------------------------------------------------------------------------
    print("\n[Check 1: Model Loading & System Health]")
    health_resp = client.get("/health")
    print(f"  -> Health Endpoint Status: {health_resp.status_code}")
    print(f"  -> Health Payload: {json.dumps(health_resp.json(), indent=2)}")
    assert health_resp.status_code == 200
    assert health_resp.json()["ml_model_loaded"] is True, "LightGBM model failed to load into memory!"
    print("  -> RESULT: [PASS] ML Model successfully loaded in memory upon startup.")

    # --------------------------------------------------------------------------
    # Check 2: Extreme Out-of-Bounds Payload (T=85°C, RH=150%, Moisture=1.5)
    # --------------------------------------------------------------------------
    print("\n[Check 2: Corrupted Out-of-Bounds Physical Data (T=85°C, RH=150%)]")
    corrupted_payload = {
        "location_label": "Thermal Extremity Zone",
        "atmosphere": {
            "temp_c": 85.0,        # Exceeds max 65.0°C physical bound
            "solar_rad_mj": 25.0,
            "rh_pct": 150.0,       # Exceeds max 100.0% physical bound
            "wind_speed_ms": 3.0,
            "precip_mm": 0.0,
            "elevation_m": 100.0,
            "latitude_deg": 16.0
        },
        "soil": {
            "soil_type": "loam",
            "volumetric_moisture": 1.5  # Exceeds max 0.9 physical bound
        },
        "crop": {
            "crop_type": "sugarcane",
            "growth_stage": "average"
        }
    }

    resp_corrupted = client.post("/api/v1/cwf/predict", json=corrupted_payload)
    print(f"  -> HTTP Response Code: {resp_corrupted.status_code} (Expected: 422 Unprocessable Entity)")
    print(f"  -> Error Response Body:")
    print(json.dumps(resp_corrupted.json(), indent=2))

    assert resp_corrupted.status_code == 422, f"Expected 422, got {resp_corrupted.status_code}"
    
    # Verify exact error locations caught by Pydantic
    errors = resp_corrupted.json().get("detail", [])
    error_fields = [e["loc"][-1] for e in errors]
    print(f"  -> Pydantic Intercepted Fields: {error_fields}")
    assert "temp_c" in error_fields, "Pydantic missed temp_c validation"
    assert "rh_pct" in error_fields, "Pydantic missed rh_pct validation"
    assert "volumetric_moisture" in error_fields, "Pydantic missed volumetric_moisture validation"
    print("  -> RESULT: [PASS] Clean 422 Validation Error returned; prevented bad data from reaching normalization engine.")

    # --------------------------------------------------------------------------
    # Check 3: Corrupted Missing Key Payload
    # --------------------------------------------------------------------------
    print("\n[Check 3: Missing Required Physical Payload Keys]")
    missing_key_payload = {
        "atmosphere": {
            "temp_c": 28.0
            # Missing solar_rad_mj, rh_pct, etc.
        }
        # Missing soil and crop
    }
    resp_missing = client.post("/api/v1/cwf/predict", json=missing_key_payload)
    print(f"  -> HTTP Response Code: {resp_missing.status_code} (Expected: 422)")
    assert resp_missing.status_code == 422
    print("  -> RESULT: [PASS] Missing structural blocks intercepted immediately.")

    # --------------------------------------------------------------------------
    # Check 4: Valid Payload Execution
    # --------------------------------------------------------------------------
    print("\n[Check 4: Valid Payload Normalization & Inference]")
    valid_payload = {
        "location_label": "Kolhapur Sugarcane Farm",
        "atmosphere": {
            "temp_c": 28.5,
            "solar_rad_mj": 21.0,
            "rh_pct": 65.0,
            "wind_speed_ms": 2.8,
            "precip_mm": 5.0,
            "elevation_m": 570.0,
            "latitude_deg": 16.7,
            "day_of_year": 200,
            "hour_of_day": 12
        },
        "soil": {
            "soil_type": "clay_loam",
            "volumetric_moisture": 0.28
        },
        "crop": {
            "crop_type": "sugarcane",
            "growth_stage": "mid"
        }
    }

    resp_valid = client.post("/api/v1/cwf/predict", json=valid_payload)
    print(f"  -> HTTP Response Code: {resp_valid.status_code}")
    print(f"  -> Valid Prediction Response:")
    print(json.dumps(resp_valid.json(), indent=2))
    assert resp_valid.status_code == 200
    print("  -> RESULT: [PASS] Valid payload processed through full decoupled ML pipeline.")
    print("\n" + "=" * 80)
    print(" ALL RESILIENCE AND VALIDATION STRESS-TESTS PASSED (4/4)")
    print("=" * 80)

if __name__ == "__main__":
    run_resilience_stress_tests()
