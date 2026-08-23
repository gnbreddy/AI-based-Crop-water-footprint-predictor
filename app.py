import os
from flask import Flask, send_from_directory, jsonify, request

app = Flask(__name__, static_folder='web', static_url_path='')

@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('web', path)

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n=======================================================")
    print(f" AquaCrop AI Web Server Started on http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host='127.0.0.1', port=port, debug=False)
