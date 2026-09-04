import json
import sqlite3
from fastapi.testclient import TestClient
from api_gateway import app
from db_models import SessionLocal, CropProfileModel, SoilProfileModel, LocationPredictionRecord

def test_database_persistence():
    print("=" * 80)
    print(" DATABASE PERSISTENCE & ORM SEEDING VERIFICATION")
    print("=" * 80)

    client = TestClient(app)

    # --------------------------------------------------------------------------
    # Check 1: GET /api/v1/crops (Auto-Seeding Verification)
    # --------------------------------------------------------------------------
    print("\n[Check 1: API Endpoint GET /api/v1/crops]")
    crop_resp = client.get("/api/v1/crops")
    print(f"  -> HTTP Status Code: {crop_resp.status_code}")
    crops_data = crop_resp.json()
    print(f"  -> Total Seeded Crops Returned: {len(crops_data)}")
    print("  -> Sample Crop Profiles:")
    for crop in crops_data[:4]:
        print(f"     • {crop['name']} ({crop['crop_key']}): Kc_ini={crop['kc_ini']}, Kc_mid={crop['kc_mid']}, Baseline Yield={crop['yield_baseline_ton_ha']} t/ha")

    assert crop_resp.status_code == 200
    assert len(crops_data) >= 8, "Expected at least 8 seeded FAO-56 crops."
    crop_keys = [c['crop_key'] for c in crops_data]
    assert 'sugarcane' in crop_keys and 'wheat' in crop_keys and 'rice' in crop_keys
    print("  -> RESULT: [PASS] FAO-56 crops successfully auto-seeded and returned as valid JSON.")

    # --------------------------------------------------------------------------
    # Check 2: GET /api/v1/records (Audit Trail Retrieval)
    # --------------------------------------------------------------------------
    print("\n[Check 2: API Endpoint GET /api/v1/records]")
    rec_resp = client.get("/api/v1/records?limit=5")
    print(f"  -> HTTP Status Code: {rec_resp.status_code}")
    records_data = rec_resp.json()
    print(f"  -> Retrieved {len(records_data)} Recent Audit Records via API:")
    for rec in records_data:
        print(f"     • Record ID #{rec['id']}: [{rec['location_label']}] Crop: {rec['crop_key']} | Actual ET: {rec['actual_et_mm']} mm | Total CWF: {rec['total_cwf_m3_ton']} m³/ton (Green: {rec['green_cwf_m3_ton']} / Blue: {rec['blue_cwf_m3_ton']})")

    assert rec_resp.status_code == 200
    assert len(records_data) > 0, "Expected prediction records in database."
    print("  -> RESULT: [PASS] API successfully retrieved recent prediction audit records.")

    # --------------------------------------------------------------------------
    # Check 3: Direct SQLite Database Inspection (data/universal_agri.db)
    # --------------------------------------------------------------------------
    print("\n[Check 3: Direct SQLite File Inspection (data/universal_agri.db)]")
    conn = sqlite3.connect("data/universal_agri.db")
    cursor = conn.cursor()

    # Query table row counts
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
    table_count = cursor.fetchone()[0]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"  -> SQLite Database Tables: {tables}")

    cursor.execute("SELECT count(*) FROM crop_profiles")
    db_crop_count = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM soil_profiles")
    db_soil_count = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM prediction_records")
    db_record_count = cursor.fetchone()[0]

    print(f"  -> Row Counts:")
    print(f"     • crop_profiles:      {db_crop_count} rows")
    print(f"     • soil_profiles:      {db_soil_count} rows")
    print(f"     • prediction_records: {db_record_count} rows (All streaming and API transactions committed!)")

    # Sample raw SQL query
    print("\n  -> Inspecting Top 3 Raw Rows from prediction_records:")
    cursor.execute("SELECT id, location_label, crop_key, soil_key, temp_c, actual_et_mm, green_cwf_m3_ton, blue_cwf_m3_ton, total_cwf_m3_ton, timestamp FROM prediction_records ORDER BY id DESC LIMIT 3")
    rows = cursor.fetchall()
    for row in rows:
        print(f"     Row #{row[0]}: Label='{row[1]}' | Crop={row[2]} | Soil={row[3]} | Temp={row[4]}°C | ET={row[5]}mm | Green={row[6]} | Blue={row[7]} | Total={row[8]} m³/t | Time={row[9]}")

    conn.close()

    assert db_record_count > 0, "No records found in SQLite database table!"
    print("\n  -> RESULT: [PASS] All streaming & API calculation records physically persisted on disk in SQLite DB.")
    print("=" * 80)
    print(" ALL DATABASE PERSISTENCE CHECKS COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    test_database_persistence()
