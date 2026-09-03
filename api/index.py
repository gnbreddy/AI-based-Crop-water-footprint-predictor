import os
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/predict_scenario', methods=['POST'])
@app.route('/predict_scenario', methods=['POST'])
def predict_scenario():
    """
    Vercel Serverless API endpoint for custom live model inference and scenario projections.
    """
    data = request.get_json() or {}
    year_horizon = int(data.get('yearHorizon', data.get('targetYear', 2050)))
    duration_mode = data.get('durationMode', 'annual')
    crop_type = data.get('crop', 'sugarcane').lower()
    
    # Regional baselines
    regional_baselines = {
        'sugarcane': {'base_et': 6661.3, 'base_rain': 1929.2, 'season_days': 360},
        'cotton': {'base_et': 7450.0, 'base_rain': 45.0, 'season_days': 180},
        'wheat': {'base_et': 5200.0, 'base_rain': 780.0, 'season_days': 140},
        'rice': {'base_et': 6100.0, 'base_rain': 2200.0, 'season_days': 120}
    }
    reg = regional_baselines.get(crop_type, regional_baselines['sugarcane'])
    
    temp_delta = float(data.get('tempDelta', 2.0))
    solar_delta = float(data.get('solarDelta', 5.0))
    precip_delta = float(data.get('precipDelta', -10.0))
    alpha = float(data.get('alpha', 0.90))
    crop_yield = float(data.get('yield', 150.0))
    kc = float(data.get('kc', 0.50))

    # Scale according to target year horizon
    years_ahead = max(1, year_horizon - 2025)
    progress = min(1.0, years_ahead / 25.0)

    cur_temp = temp_delta * progress
    cur_solar = solar_delta * progress
    cur_precip = precip_delta * progress

    # Time period duration scaling
    duration_ratio = (reg['season_days'] / 365.25) if duration_mode == 'growing_season' else 1.0

    base_et = reg['base_et'] * duration_ratio
    projected_et = base_et * (1.0 + 0.045 * cur_temp + (cur_solar / 100.0))
    et_crop = kc * projected_et

    base_rain = reg['base_rain'] * duration_ratio
    projected_rain = base_rain * (1.0 + (cur_precip / 100.0))
    effective_rain = alpha * projected_rain

    green_water_et = min(et_crop, effective_rain)
    blue_water_et = max(0.0, et_crop - effective_rain)

    green_cwf = (10.0 * green_water_et) / crop_yield
    blue_cwf = (10.0 * blue_water_et) / crop_yield
    total_cwf = green_cwf + blue_cwf

    return jsonify({
        'status': 'success',
        'year_horizon': year_horizon,
        'duration_mode': duration_mode,
        'duration_days': reg['season_days'] if duration_mode == 'growing_season' else 365.25,
        'projected_annual_et_mm': round(projected_et, 1),
        'green_water_footprint_m3_ton': round(green_cwf, 2),
        'blue_water_footprint_m3_ton': round(blue_cwf, 2),
        'total_water_footprint_m3_ton': round(total_cwf, 2),
        'irrigation_stress_level': 'High Stress' if blue_cwf > 190.0 else 'Moderate'
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'AquaCrop AI Vercel Engine'})

# For local development
if __name__ == '__main__':
    app.run(port=5000)
