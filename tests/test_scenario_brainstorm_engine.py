"""
Comprehensive Test Suite for the Zero-Friction 3-Way Quantile Forecast Engine
and Biophysical Factors brainstormed in brainstorm/ALGORITHM_BRAINSTORM.md.
"""

import pytest
import os
import glob
from fastapi.testclient import TestClient
from climatology_engine import ClimatologyScenarioEngine, HORIZON_DAYS_MAP, CROP_TRAITS
from api_gateway import app as fastapi_app
from app import app as flask_app
import compiler

def test_climatology_dataset_integrity():
    """Verify that all 26 authentic annual datasets (2000-2025) are present on disk."""
    csv_files = sorted(glob.glob("data/cwf_kolhapur_*.csv"))
    assert len(csv_files) >= 26, f"Expected 26 datasets, found {len(csv_files)}"
    
    # Check that each file has >= 10,000 records
    import pandas as pd
    for f in csv_files:
        df = pd.read_csv(f)
        assert len(df) >= 10000, f"File {f} has only {len(df)} rows, expected >= 10,000"
        assert 'datetime' in df.columns, f"Missing datetime in {f}"
        assert 'temp_c' in df.columns, f"Missing temp_c in {f}"
        assert 'et0_fao56_mm' in df.columns, f"Missing et0_fao56_mm in {f}"

def test_climatology_scenario_engine_quantiles():
    """Verify empirical quantile retrieval from 25-year archive."""
    engine = ClimatologyScenarioEngine()
    quantiles = engine.get_climatology_quantiles(day_of_year=180)
    assert 'normal' in quantiles
    assert 'drought' in quantiles
    assert 'flood' in quantiles

    # Meteorological consistency checks: Drought should have higher temp and VPD than flood
    assert quantiles['drought']['temp_c'] > quantiles['flood']['temp_c']
    assert quantiles['drought']['vpd_kpa'] > quantiles['flood']['vpd_kpa']
    assert quantiles['flood']['precip'] > quantiles['drought']['precip']

def test_three_way_triad_scenarios():
    """Verify 3-way quantile predictions for normal, drought, and flood."""
    engine = ClimatologyScenarioEngine()
    res = engine.predict_scenario_triad(
        location='kolhapur',
        crop_type='sugarcane',
        time_horizon='1_year',
        enso_phase='neutral'
    )
    assert res['status'] == 'success'
    scenarios = res['scenarios']
    
    normal = scenarios['baseline_normal']
    drought = scenarios['drought_stress']
    flood = scenarios['flood_excess']

    # Blue water in drought must be substantially higher than in normal
    assert drought['cwf_blue_m3_ton'] > normal['cwf_blue_m3_ton']
    # Blue water in flood should approach near-zero
    assert flood['cwf_blue_m3_ton'] < normal['cwf_blue_m3_ton']
    # Total CWF in drought should be elevated due to yield penalty in denominator
    assert drought['cwf_total_m3_ton'] > normal['cwf_total_m3_ton']

def test_biophysical_factors():
    """Verify GDD, dynamic root depth, Dual Kc, and capillary upflux."""
    engine = ClimatologyScenarioEngine()
    res = engine.predict_scenario_triad('kolhapur', 'sugarcane', '1_year')
    bio = res['biophysical_diagnostics']

    assert 'accumulated_gdd' in bio
    assert bio['accumulated_gdd'] > 0
    assert 'phenological_stage' in bio
    assert bio['dynamic_root_depth_m'] >= 0.20
    assert bio['dynamic_root_depth_m'] <= 1.20
    assert 'dual_kc_normal' in bio
    assert bio['dual_kc_normal']['kcb'] > 0
    assert bio['dual_kc_normal']['ke'] > 0
    
    # Verify capillary upflux hydration
    assert res['scenarios']['baseline_normal']['capillary_upflux_mm'] > 0

def test_stewart_yield_and_economic_valuation():
    """Verify FAO-33 Stewart yield deficit equation and financial impact."""
    engine = ClimatologyScenarioEngine()
    res = engine.predict_scenario_triad('kolhapur', 'sugarcane', '1_year')
    drought = res['scenarios']['drought_stress']

    assert drought['yield_loss_pct'] > 0
    assert drought['actual_yield_ton_ha'] < 105.0
    assert drought['yield_loss_ton_ha'] > 0
    assert drought['revenue_loss_inr_ha'] > 0
    # Expected sugarcane FRP ~3150 Rs/ton
    expected_revenue_loss = drought['yield_loss_ton_ha'] * 3150.0
    assert abs(drought['revenue_loss_inr_ha'] - expected_revenue_loss) < 5.0

def test_macro_climate_teleconnections():
    """Verify ENSO phase shifting on probability distribution."""
    engine = ClimatologyScenarioEngine()
    
    res_el_nino = engine.predict_scenario_triad('kolhapur', 'sugarcane', '1_year', enso_phase='el_nino')
    res_la_nina = engine.predict_scenario_triad('kolhapur', 'sugarcane', '1_year', enso_phase='la_nina')
    
    p_el_nino = res_el_nino['probability_distribution']
    p_la_nina = res_la_nina['probability_distribution']

    # El Niño should shift drought risk up
    assert p_el_nino['drought_pct'] > p_la_nina['drought_pct']
    # La Niña should shift flood risk up
    assert p_la_nina['flood_pct'] > p_el_nino['flood_pct']

def test_fastapi_scenario_predict_endpoint():
    """Verify FastAPI /api/v1/cwf/scenario-predict endpoint."""
    client = TestClient(fastapi_app)
    response = client.post("/api/v1/cwf/scenario-predict", json={
        "location": "kolhapur",
        "crop_type": "sugarcane",
        "time_horizon": "1_year",
        "enso_phase": "neutral"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "scenarios" in data
    assert "baseline_normal" in data["scenarios"]
    assert "drought_stress" in data["scenarios"]
    assert "flood_excess" in data["scenarios"]
    assert "hazard_assessment" in data

def test_flask_scenario_predict_endpoint():
    """Verify Flask /api/v1/cwf/scenario-predict endpoint."""
    client = flask_app.test_client()
    response = client.post("/api/v1/cwf/scenario-predict", json={
        "location": "kolhapur",
        "crop_type": "sugarcane",
        "time_horizon": "1_month",
        "enso_phase": "el_nino"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["query_context"]["time_horizon"] == "1_month"
    assert data["probability_distribution"]["drought_pct"] == 38

def test_operational_disruption_is_explicit_and_assumption_led():
    """A pandemic-style case must never be inferred from climate data alone."""
    engine = ClimatologyScenarioEngine()
    res = engine.predict_scenario_triad(
        'kolhapur', 'sugarcane', '1_year',
        rare_event='pandemic_disruption',
        irrigation_access_fraction=0.60,
        yield_disruption_fraction=0.20,
        event_evidence_note='Farm survey: labour and irrigation access disrupted.'
    )
    event = res['rare_event_assessment']
    case = res['scenarios']['operational_disruption']
    normal = res['scenarios']['baseline_normal']

    assert event['active'] is True
    assert 'Not inferred from calendar year' in event['inference_policy']
    assert case['rare_event_assumption_led'] is True
    assert case['irrigation_access_fraction'] == 0.60
    assert case['unmet_blue_water_m3_ton'] > 0
    assert case['actual_yield_ton_ha'] < normal['actual_yield_ton_ha']
    assert case['cwf_total_m3_ton'] > normal['cwf_total_m3_ton']

def test_no_operational_disruption_case_without_explicit_request():
    engine = ClimatologyScenarioEngine()
    res = engine.predict_scenario_triad('kolhapur', 'sugarcane', '1_year')
    assert res['rare_event_assessment']['active'] is False
    assert 'operational_disruption' not in res['scenarios']

def test_fastapi_preserves_explicit_operational_disruption_response():
    client = TestClient(fastapi_app)
    response = client.post('/api/v1/cwf/scenario-predict', json={
        'location': 'kolhapur',
        'crop_type': 'sugarcane',
        'time_horizon': '1_year',
        'rare_event': 'pandemic_disruption',
        'irrigation_access_fraction': 0.7,
        'yield_disruption_fraction': 0.1,
    })
    assert response.status_code == 200
    data = response.json()
    assert data['rare_event_assessment']['active'] is True
    assert 'operational_disruption' in data['scenarios']
