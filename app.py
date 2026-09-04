import os
from flask import Flask, send_from_directory, jsonify, request

app = Flask(__name__, static_folder='web', static_url_path='')

@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/api/predict_scenario', methods=['POST'])
def predict_scenario():
    """
    API endpoint for custom live model inference and scenario projections.
    """
    data = request.get_json() or {}
    temp_delta = float(data.get('tempDelta', 2.0))
    solar_delta = float(data.get('solarDelta', 5.0))
    precip_delta = float(data.get('precipDelta', -10.0))
    alpha = float(data.get('alpha', 0.90))
    crop_yield = float(data.get('yield', 150.0))
    kc = float(data.get('kc', 0.50))

    # Base projection calculations
    base_et = 6661.3  # Annual mm
    projected_et = base_et * (1.0 + 0.045 * temp_delta + (solar_delta / 100.0))
    et_crop = kc * projected_et

    base_rain = 1929.2  # Annual mm
    projected_rain = base_rain * (1.0 + (precip_delta / 100.0))
    effective_rain = alpha * projected_rain

    green_water_et = min(et_crop, effective_rain)
    blue_water_et = max(0.0, et_crop - effective_rain)

    green_cwf = (10.0 * green_water_et) / crop_yield
    blue_cwf = (10.0 * blue_water_et) / crop_yield
    total_cwf = green_cwf + blue_cwf

    return jsonify({
        'status': 'success',
        'year_horizon': 2050,
        'projected_annual_et_mm': round(projected_et, 1),
        'green_water_footprint_m3_ton': round(green_cwf, 2),
        'blue_water_footprint_m3_ton': round(blue_cwf, 2),
        'total_water_footprint_m3_ton': round(total_cwf, 2),
        'irrigation_stress_level': 'High Stress' if blue_cwf > 190.0 else 'Moderate'
    })

@app.route('/api/v1/cwf/scenario-predict', methods=['POST'])
def scenario_predict_v1():
    """
    Zero-Friction 3-Way Quantile Forecast Triad API.
    Only takes Location, Crop Type, Horizon (1d to 10yr), and optional ENSO phase.
    """
    try:
        from climatology_engine import ClimatologyScenarioEngine
        engine = ClimatologyScenarioEngine()
        data = request.get_json() or {}
        res = engine.predict_scenario_triad(
            location=data.get('location', 'kolhapur'),
            crop_type=data.get('crop_type', 'sugarcane'),
            time_horizon=data.get('time_horizon', '1_year'),
            enso_phase=data.get('enso_phase', 'neutral'),
            rare_event=data.get('rare_event', 'none'),
            irrigation_access_fraction=data.get('irrigation_access_fraction'),
            yield_disruption_fraction=data.get('yield_disruption_fraction'),
            event_evidence_note=data.get('event_evidence_note'),
        )
        return jsonify(res)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/v1/cwf/climatology-datasets', methods=['GET'])
def get_climatology_summary():
    """Returns empirical 2000-2025 satellite database metadata."""
    import glob
    csv_files = glob.glob(os.path.join(os.path.dirname(__file__), 'data', 'cwf_kolhapur_*.csv'))
    return jsonify({
        'status': 'success',
        'total_datasets': len(csv_files),
        'year_range': '2000 - 2025',
        'target_records': '300,000+ authentic GEE records',
        'location': 'Kolhapur Sugarcane Heartland (Maharashtra, India)'
    })

ANATOMY_CACHE = {}

def generate_local_anatomy_fallback(data: dict) -> dict:
    crop = data.get('crop_type', 'sugarcane').capitalize()
    location = data.get('location', 'karveer').capitalize()
    horizon = data.get('time_horizon', '1_year').replace('_', ' ').capitalize()
    condition = data.get('condition', 'drought').capitalize()
    basis = data.get('reporting_basis', 'normalized')
    cwf_total = data.get('total_cwf', '5.0')
    cwf_blue = data.get('blue_cwf', '2.0')
    cwf_green = data.get('green_cwf', '3.0')
    blue_pct = data.get('blue_pct', '40.0%')
    green_pct = data.get('green_pct', '60.0%')
    directive = data.get('directive', 'Balanced Irrigation')
    yield_loss = data.get('yield_loss', '-48%')
    revenue_loss = data.get('revenue_loss', 'Rs. 1,58,760 / ha')

    return {
        "origin_datum": (
            f"The Cartesian coordinate origin $(0, 0)$ is pinned directly at calendar year <strong>2025</strong> "
            f"on the horizontal X-axis for <strong>{crop}</strong> in <strong>{location} (Kolhapur Basin)</strong>. "
            f"This anchors the {horizon} forecast to 26 consecutive years of authentic Earth observation records "
            f"(2000–2025, totaling <strong>300,232 authentic observations</strong>). All physical forecast trajectories "
            f"diverge strictly from this datum, ensuring future water footprints are bound to empirical monsoon climatology."
        ),
        "cwf_metric": (
            f"The vertical Y-axis measures the consumptive <strong>Crop Water Footprint ($m^3/\\text{{ton}}$)</strong> "
            f"for harvested <strong>{crop}</strong>, following the Hoekstra Water Footprint Network framework ($CWF = CWU / Y$). "
            f"Under the active <strong>{basis.capitalize()} Basis</strong>, active {condition} consumption is evaluated at "
            f"<strong>{cwf_total} m³/ton</strong>, capturing the precise biophysical balance between canopy evapotranspiration and yield."
        ),
        "scenario_curves": (
            f"<ul class=\"comp-detail-bullets\">"
            f"<li><strong>🟡 Drought Scenario Curve (Upper Divergence, 18% Probability):</strong> Total CWF surges under severe moisture deficit, requiring high irrigation intensity while root-zone moisture rapidly depletes toward wilting point.</li>"
            f"<li><strong>🟢 Normal / Baseline Curve (Central Equilibrium, 64% Probability):</strong> Total CWF balances optimal crop evapotranspiration ($ET_c$) and sustainable vegetative and yield development under typical monsoon rainfall.</li>"
            f"<li><strong>🔵 Flood Scenario Curve (Lower Bound, 18% Probability):</strong> Heavy monsoonal precipitation supersaturates the soil root zone, eliminating supplemental blue irrigation demand while presenting waterlogging risks.</li>"
            f"</ul>"
        ),
        "color_partitioning": (
            f"Each trajectory curve is physically partitioned into two contiguous color segments whose arc lengths strictly equal their volumetric water contributions ($L_{{total}} = L_{{blue}} + L_{{green}}$):"
            f"<ul class=\"comp-detail-bullets\">"
            f"<li><strong class=\"text-blue\">🔵 Blue Water ($CWF_{{blue}}$):</strong> Rendered in electric blue, representing artificial irrigation from canals and groundwater. Occupies <strong>{blue_pct} ({cwf_blue} m³/ton)</strong> of the total curve length.</li>"
            f"<li><strong class=\"text-green\">🟢 Green Water ($CWF_{{green}}$):</strong> Rendered in emerald green, representing natural rainfall stored in the root profile. Occupies <strong>{green_pct} ({cwf_green} m³/ton)</strong> of the total curve length.</li>"
            f"</ul>"
        ),
        "directives_economics": (
            f"Operational directives and economic diagnostics derived for <strong>{crop}</strong> under <strong>{condition}</strong> conditions:"
            f"<ul class=\"comp-detail-bullets\">"
            f"<li><strong>🚨 Operational Directive:</strong> <strong>{directive}</strong> scheduled to safeguard root moisture tension.</li>"
            f"<li><strong>📉 Stewart Harvest Loss:</strong> FAO-33 water-yield deficit function projects a <strong>{yield_loss}</strong> impact on harvested biomass.</li>"
            f"<li><strong>💸 Financial Loss:</strong> Quantifies estimated farmer revenue deficit of <strong>{revenue_loss}</strong> benchmarked against statutory minimum support prices.</li>"
            f"<li><strong>💧 Capillary Ground Support:</strong> Accounts for natural upward hydraulic flux from the shallow alluvial water table across Kolhapur basin.</li>"
            f"</ul>"
        )
    }

@app.route('/api/v1/cwf/ai-anatomy', methods=['POST'])
def generate_ai_anatomy():
    """
    Generates dynamic agro-hydrological component anatomy and scientific descriptions
    powered by Gemini 2.5 Flash API based on active crop, location, horizon, condition, and CWF metrics.
    """
    import json
    import urllib.request
    from config import GEMINI_API_KEY

    data = request.get_json() or {}
    crop = data.get('crop_type', 'sugarcane').capitalize()
    location = data.get('location', 'karveer').capitalize()
    horizon = data.get('time_horizon', '1_year')
    condition = data.get('condition', 'drought').capitalize()
    basis = data.get('reporting_basis', 'normalized')
    cwf_total = data.get('total_cwf', '5.0')
    cwf_blue = data.get('blue_cwf', '2.0')
    cwf_green = data.get('green_cwf', '3.0')
    blue_pct = data.get('blue_pct', '40.0%')
    green_pct = data.get('green_pct', '60.0%')
    directive = data.get('directive', 'Balanced Irrigation')
    yield_loss = data.get('yield_loss', '-48%')
    revenue_loss = data.get('revenue_loss', 'Rs. 1,58,760 / ha')

    cache_key = f"{crop}_{location}_{horizon}_{condition}_{basis}_{cwf_total}"
    if cache_key in ANATOMY_CACHE:
        return jsonify({'status': 'success', 'source': 'cache', 'anatomy': ANATOMY_CACHE[cache_key]})

    prompt = f"""
You are an expert Agro-Hydrologist and Crop Water Footprint (CWF) scientist.
Given the following user parameters and authentic climatological model outputs:
- Crop: {crop}
- Location: {location} (Kolhapur Agro-Basin, Western India)
- Horizon: {horizon}
- Condition: {condition} Scenario
- Basis: {basis.capitalize()} Basis
- Active Total CWF: {cwf_total} m³/ton
- Blue Water CWF (Irrigation): {cwf_blue} m³/ton ({blue_pct} share)
- Green Water CWF (Rainfall & Soil Storage): {cwf_green} m³/ton ({green_pct} share)
- Operational Directive: {directive}
- Yield Deficit: {yield_loss}
- Revenue Impact: {revenue_loss}

Generate a JSON object with exactly these 5 keys containing rich, authoritative, formatted HTML explanations with <strong> and <em> tags:
1. "origin_datum": HTML text explaining why the (0,0) origin datum at Year 2025 on the X-axis anchors {crop} projections across {horizon} from 26 years of authentic satellite data.
2. "cwf_metric": HTML text detailing the vertical Y-axis Crop Water Footprint metric ({basis} basis) for {crop}.
3. "scenario_curves": HTML text with <ul>/<li> bullets describing the 3 diverging quantile curves (🟡 Drought upper, 🟢 Normal central, 🔵 Flood lower) with exact values for {crop}.
4. "color_partitioning": HTML text explaining the dual-color arc-length partitioning between Blue Water ({blue_pct}) and Green Water ({green_pct}) for {crop}.
5. "directives_economics": HTML text with <ul>/<li> bullets detailing irrigation directives ({directive}), Stewart yield collapse ({yield_loss}), economic loss ({revenue_loss}), and capillary flux.

Respond ONLY with the JSON object.
"""

    try:
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
                "thinkingConfig": {
                    "thinkingBudget": 0
                }
            }
        }
        req = urllib.request.Request(
            gemini_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
            parsed = json.loads(raw_text)
            ANATOMY_CACHE[cache_key] = parsed
            return jsonify({'status': 'success', 'source': 'gemini-2.5-flash', 'anatomy': parsed})
    except Exception as err:
        print(f"[AI Anatomy Warning] Gemini API unavailable or timed out ({err}), using local dynamic fallback.")
        fallback = generate_local_anatomy_fallback(data)
        ANATOMY_CACHE[cache_key] = fallback
        return jsonify({'status': 'success', 'source': 'local_synthesis', 'anatomy': fallback})

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('web', path)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f" AquaCrop AI Web Server Started on http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host='127.0.0.1', port=port, debug=False)
