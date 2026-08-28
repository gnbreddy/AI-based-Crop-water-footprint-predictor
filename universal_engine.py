import os
import math
import numpy as np
import pandas as pd
import joblib

from schemas import (
    AtmosphericPayload,
    SoilPayload,
    CropPayload,
    UniversalIngestionRequest,
    UniversalPredictionResponse,
    ThermodynamicDiagnostics,
    EvapotranspirationDepths,
    CropWaterFootprintOutput
)
from normalization_engine import PhysicalNormalizationEngine
from crop_repository import CropSoilRepository
from db_models import SessionLocal, LocationPredictionRecord

# Export static reference dictionaries for backwards compatibility
SOIL_DATABASE = {
    'sandy_loam': {'field_capacity_fc': 0.18, 'wilting_point_wp': 0.08, 'infiltration_alpha': 0.90, 'description': 'Coarse-textured loam'},
    'loam': {'field_capacity_fc': 0.28, 'wilting_point_wp': 0.14, 'infiltration_alpha': 0.88, 'description': 'Balanced medium texture'},
    'clay_loam': {'field_capacity_fc': 0.32, 'wilting_point_wp': 0.18, 'infiltration_alpha': 0.82, 'description': 'Fine-medium texture'},
    'clay': {'field_capacity_fc': 0.38, 'wilting_point_wp': 0.22, 'infiltration_alpha': 0.72, 'description': 'Heavy clay'},
    'silt_loam': {'field_capacity_fc': 0.30, 'wilting_point_wp': 0.12, 'infiltration_alpha': 0.85, 'description': 'High available water'},
    'sand': {'field_capacity_fc': 0.12, 'wilting_point_wp': 0.04, 'infiltration_alpha': 0.95, 'description': 'Very coarse sand'}
}

CROP_DATABASE = {
    'sugarcane': {'kc_ini': 0.40, 'kc_mid': 1.25, 'kc_end': 0.75, 'kc_avg': 0.50, 'yield_baseline_ton_ha': 150.0, 'root_depth_m': 1.5, 'depletion_fraction_p': 0.65, 'name': 'Sugarcane'},
    'cotton': {'kc_ini': 0.35, 'kc_mid': 1.20, 'kc_end': 0.60, 'kc_avg': 0.85, 'yield_baseline_ton_ha': 3.5, 'root_depth_m': 1.2, 'depletion_fraction_p': 0.65, 'name': 'Cotton'},
    'wheat': {'kc_ini': 0.30, 'kc_mid': 1.15, 'kc_end': 0.40, 'kc_avg': 0.90, 'yield_baseline_ton_ha': 5.0, 'root_depth_m': 1.0, 'depletion_fraction_p': 0.55, 'name': 'Wheat'},
    'rice': {'kc_ini': 1.05, 'kc_mid': 1.20, 'kc_end': 0.90, 'kc_avg': 1.15, 'yield_baseline_ton_ha': 4.5, 'root_depth_m': 0.6, 'depletion_fraction_p': 0.20, 'name': 'Rice'},
    'maize': {'kc_ini': 0.30, 'kc_mid': 1.20, 'kc_end': 0.50, 'kc_avg': 0.85, 'yield_baseline_ton_ha': 8.5, 'root_depth_m': 1.2, 'depletion_fraction_p': 0.55, 'name': 'Maize / Corn'},
    'soybean': {'kc_ini': 0.40, 'kc_mid': 1.15, 'kc_end': 0.50, 'kc_avg': 0.80, 'yield_baseline_ton_ha': 3.2, 'root_depth_m': 0.9, 'depletion_fraction_p': 0.50, 'name': 'Soybean'},
    'potato': {'kc_ini': 0.50, 'kc_mid': 1.15, 'kc_end': 0.75, 'kc_avg': 0.85, 'yield_baseline_ton_ha': 35.0, 'root_depth_m': 0.6, 'depletion_fraction_p': 0.35, 'name': 'Potato'},
    'tomato': {'kc_ini': 0.60, 'kc_mid': 1.15, 'kc_end': 0.80, 'kc_avg': 0.90, 'yield_baseline_ton_ha': 50.0, 'root_depth_m': 0.8, 'depletion_fraction_p': 0.40, 'name': 'Tomato'}
}

class UniversalCropWaterFootprintEngine:
    """
    Universal, Location-Agnostic Agro-Hydrological Prediction Engine.
    
    Accepts standardized physical payloads, translates raw meteorology into
    dimensionless thermodynamic ratios, and outputs verified Green, Blue, and
    Total Crop Water Footprints (m³/ton) for any coordinate on Earth.
    """
    def __init__(self, model_path=None):
        from config import FINAL_MODEL_PATH
        if model_path is None:
            model_path = FINAL_MODEL_PATH
        
        self.norm = PhysicalNormalizationEngine()
        self.repo = CropSoilRepository()
        self.model_path = model_path
        self.model = None
        self.load_production_model()

    def load_production_model(self):
        """Loads or hot-reloads the active production LightGBM model from disk."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print(f"[Universal Engine] Successfully loaded production model from {self.model_path}")
            except Exception as e:
                print(f"[Universal Engine] Notice: Running with analytical FAO-56 engine ({e})")
                self.model = None

    def reload_model(self):
        """Hot-reloads the newly trained model dynamically without server restart."""
        self.load_production_model()
        return self.model is not None

    def process_payload(self, request: UniversalIngestionRequest) -> UniversalPredictionResponse:
        """
        Processes a strictly typed Pydantic request and returns a structured response.
        """
        raw_res = self.analyze_location(
            temp_c=request.atmosphere.temp_c,
            solar_rad_mj=request.atmosphere.solar_rad_mj,
            precip_mm=request.atmosphere.precip_mm,
            soil_moisture=request.soil.volumetric_moisture,
            rh_pct=request.atmosphere.rh_pct,
            wind_speed_ms=request.atmosphere.wind_speed_ms,
            elevation_m=request.atmosphere.elevation_m,
            latitude_deg=request.atmosphere.latitude_deg,
            day_of_year=request.atmosphere.day_of_year,
            crop_type=request.crop.crop_type,
            soil_type=request.soil.soil_type,
            custom_kc=request.crop.custom_kc,
            custom_yield_ton_ha=request.crop.custom_yield_ton_ha,
            custom_alpha=request.soil.custom_infiltration_alpha,
            hour_of_day=request.atmosphere.hour_of_day,
            growth_stage=request.crop.growth_stage,
            custom_fc=request.soil.custom_field_capacity,
            custom_wp=request.soil.custom_wilting_point
        )

        # Log prediction to relational database
        self._log_record(request.location_label, request, raw_res)

        return UniversalPredictionResponse(
            status="success",
            location_label=request.location_label or "Custom Region",
            crop_name=raw_res['crop_context']['crop_name'],
            soil_type=raw_res['location_context']['soil_type'],
            thermodynamic_diagnostics=ThermodynamicDiagnostics(**raw_res['thermodynamic_diagnostics']),
            evapotranspiration_depths_mm=EvapotranspirationDepths(**raw_res['evapotranspiration_depth_mm']),
            crop_water_footprint_m3_ton=CropWaterFootprintOutput(**raw_res['crop_water_footprint_m3_ton']),
            irrigation_stress_assessment=raw_res['irrigation_stress_assessment']
        )

    def analyze_location(self, 
                         temp_c: float, 
                         solar_rad_mj: float, 
                         precip_mm: float, 
                         soil_moisture: float, 
                         rh_pct: float = 60.0, 
                         wind_speed_ms: float = 3.0, 
                         elevation_m: float = 100.0, 
                         latitude_deg: float = 16.0, 
                         day_of_year: int = 180, 
                         crop_type: str = 'sugarcane', 
                         soil_type: str = 'loam',
                         custom_kc: float = None, 
                         custom_yield_ton_ha: float = None, 
                         custom_alpha: float = None,
                         hour_of_day: int = 12,
                         growth_stage: str = 'average',
                         custom_fc: float = None,
                         custom_wp: float = None) -> dict:
        """
        Evaluates physical CWF for any geographic location using decoupled normalization.
        """
        # Dynamic Database Fetching
        crop_prof = self.repo.get_crop_profile(crop_type, growth_stage=growth_stage)
        soil_prof = self.repo.get_soil_profile(soil_type)

        kc = custom_kc if custom_kc is not None else crop_prof['kc_selected']
        crop_yield = custom_yield_ton_ha if custom_yield_ton_ha is not None else crop_prof['yield_baseline_ton_ha']
        alpha = custom_alpha if custom_alpha is not None else (soil_prof['infiltration_alpha'])
        fc = custom_fc if custom_fc is not None else soil_prof['field_capacity_fc']
        wp = custom_wp if custom_wp is not None else soil_prof['wilting_point_wp']

        # 1. Decoupled Dimensionless Physical Normalization
        vpd = self.norm.vapor_pressure_deficit(temp_c, rh_pct)
        ssi = self.norm.soil_water_stress_index(soil_moisture, fc, wp)
        r_a = self.norm.extraterrestrial_radiation(latitude_deg, day_of_year)
        rel_solar = self.norm.relative_solar_forcing(solar_rad_mj, latitude_deg, day_of_year)
        et0_pm = self.norm.reference_et0_penman_monteith(temp_c, solar_rad_mj, rh_pct, wind_speed_ms, elevation_m)

        # 2. Machine Learning Inference or Physics Fallback
        if self.model is not None:
            try:
                features_dict = {
                    'temp_c': temp_c,
                    'wind_speed': wind_speed_ms,
                    'pressure_kpa': 101.3 * ((293.0 - 0.0065 * elevation_m) / 293.0) ** 5.26,
                    'solar_rad': solar_rad_mj,
                    'precip': precip_mm,
                    'soil_moisture': soil_moisture,
                    'ndvi': float(np.clip(0.3 + 0.5 * ssi, 0.1, 0.9)),
                    'temp_c_lag1': temp_c - 0.5,
                    'precip_lag1': 0.0,
                    'ndvi_lag1': float(np.clip(0.3 + 0.5 * ssi, 0.1, 0.9)),
                    'soil_moisture_lag1': soil_moisture,
                    'temp_c_lag4': temp_c,
                    'soil_moisture_lag4': soil_moisture,
                    'temp_c_roll24h': temp_c,
                    'solar_rad_roll24h': solar_rad_mj,
                    'soil_moisture_roll24h': soil_moisture,
                    'precip_cum48h': precip_mm,
                    'sin_hour': math.sin(2.0 * math.pi * hour_of_day / 24.0),
                    'cos_hour': math.cos(2.0 * math.pi * hour_of_day / 24.0),
                    'sin_doy': math.sin(2.0 * math.pi * day_of_year / 365.25),
                    'cos_doy': math.cos(2.0 * math.pi * day_of_year / 365.25)
                }
                feat_df = pd.DataFrame([features_dict])
                et_pred = float(self.model.predict(feat_df)[0])
                actual_et_mm = float(np.maximum(0.05, et_pred))
            except Exception:
                actual_et_mm = float(et0_pm * kc * (0.4 + 0.6 * ssi))
        else:
            actual_et_mm = float(et0_pm * kc * (0.4 + 0.6 * ssi))

        # 3. Crop Adjusted Transpiration
        et_crop_mm = float(kc * actual_et_mm)

        # 4. Infiltration & Effective Rain
        p_eff_mm = float(alpha * precip_mm)

        # 5. Green / Blue Hydrological Partitioning
        et_green_mm = float(min(et_crop_mm, p_eff_mm))
        et_blue_mm = float(max(0.0, et_crop_mm - p_eff_mm))

        # 6. Water Footprint per Ton of Harvest Output (m³/ton)
        cwu_green_m3_ha = 10.0 * et_green_mm
        cwu_blue_m3_ha = 10.0 * et_blue_mm
        cwu_total_m3_ha = cwu_green_m3_ha + cwu_blue_m3_ha

        gwf_m3_ton = cwu_green_m3_ha / (crop_yield + 1e-6)
        bwf_m3_ton = cwu_blue_m3_ha / (crop_yield + 1e-6)
        twf_m3_ton = gwf_m3_ton + bwf_m3_ton

        green_ratio_pct = (gwf_m3_ton / (twf_m3_ton + 1e-6)) * 100.0
        blue_ratio_pct = 100.0 - green_ratio_pct

        # 7. Sustainability & Irrigation Stress Rating
        if bwf_m3_ton > 200.0 or ssi < 0.25:
            stress_level = 'Critical Irrigation Pressure'
        elif bwf_m3_ton > 100.0 or ssi < 0.50:
            stress_level = 'Moderate Irrigation Required'
        else:
            stress_level = 'Rainfed Sustainable / Low Stress'

        return {
            'location_context': {
                'latitude_deg': latitude_deg,
                'elevation_m': elevation_m,
                'day_of_year': day_of_year,
                'hour_of_day': hour_of_day,
                'soil_type': soil_type,
                'soil_description': soil_prof['description']
            },
            'crop_context': {
                'crop_name': crop_prof['name'],
                'crop_coefficient_kc': kc,
                'crop_yield_ton_ha': crop_yield,
                'effective_rain_factor_alpha': alpha,
                'growth_stage': growth_stage
            },
            'thermodynamic_diagnostics': {
                'vapor_pressure_deficit_kpa': round(vpd, 4),
                'soil_stress_index_0_1': round(ssi, 3),
                'extraterrestrial_radiation_mj': round(r_a, 2),
                'relative_solar_forcing': round(rel_solar, 3),
                'fao56_reference_et0_mm': round(et0_pm, 3)
            },
            'evapotranspiration_depth_mm': {
                'actual_et_mm': round(actual_et_mm, 3),
                'crop_adjusted_et_mm': round(et_crop_mm, 3),
                'effective_precipitation_mm': round(p_eff_mm, 3),
                'green_evapotranspiration_mm': round(et_green_mm, 3),
                'blue_evapotranspiration_mm': round(et_blue_mm, 3)
            },
            'crop_water_footprint_m3_ton': {
                'green_water_footprint_m3_ton': round(gwf_m3_ton, 2),
                'blue_water_footprint_m3_ton': round(bwf_m3_ton, 2),
                'total_water_footprint_m3_ton': round(twf_m3_ton, 2),
                'green_share_pct': round(green_ratio_pct, 1),
                'blue_share_pct': round(blue_ratio_pct, 1)
            },
            'irrigation_stress_assessment': stress_level
        }

    def _log_record(self, location_label: str, request: UniversalIngestionRequest, raw_res: dict):
        """Logs prediction calculation to SQLite/PostgreSQL audit table."""
        db = SessionLocal()
        try:
            rec = LocationPredictionRecord(
                location_label=location_label or "Custom",
                latitude_deg=request.atmosphere.latitude_deg,
                elevation_m=request.atmosphere.elevation_m,
                crop_key=request.crop.crop_type,
                soil_key=request.soil.soil_type,
                temp_c=request.atmosphere.temp_c,
                solar_rad_mj=request.atmosphere.solar_rad_mj,
                precip_mm=request.atmosphere.precip_mm,
                soil_moisture=request.soil.volumetric_moisture,
                actual_et_mm=raw_res['evapotranspiration_depth_mm']['actual_et_mm'],
                green_cwf_m3_ton=raw_res['crop_water_footprint_m3_ton']['green_water_footprint_m3_ton'],
                blue_cwf_m3_ton=raw_res['crop_water_footprint_m3_ton']['blue_water_footprint_m3_ton'],
                total_cwf_m3_ton=raw_res['crop_water_footprint_m3_ton']['total_water_footprint_m3_ton']
            )
            db.add(rec)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

if __name__ == "__main__":
    engine = UniversalCropWaterFootprintEngine()
    print("[Universal Engine] Testing Pydantic Typed Payload Ingestion...")
    
    sample_request = UniversalIngestionRequest(
        location_label="Nile Delta, Egypt",
        atmosphere=AtmosphericPayload(
            temp_c=36.0,
            solar_rad_mj=25.0,
            rh_pct=30.0,
            wind_speed_ms=4.0,
            precip_mm=0.0,
            elevation_m=15.0,
            latitude_deg=30.5
        ),
        soil=SoilPayload(
            soil_type='sandy_loam',
            volumetric_moisture=0.12
        ),
        crop=CropPayload(
            crop_type='cotton',
            growth_stage='mid'
        )
    )
    
    response = engine.process_payload(sample_request)
    print(f"\n[Location: {response.location_label} | Crop: {response.crop_name}]")
    print(f"  -> Total CWF: {response.crop_water_footprint_m3_ton.total_water_footprint_m3_ton} m³/ton")
    print(f"  -> Green: {response.crop_water_footprint_m3_ton.green_water_footprint_m3_ton} m³/ton | Blue: {response.crop_water_footprint_m3_ton.blue_water_footprint_m3_ton} m³/ton")
    print(f"  -> Stress Rating: {response.irrigation_stress_assessment}")
