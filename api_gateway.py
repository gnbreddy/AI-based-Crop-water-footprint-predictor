from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict

from db_models import (
    SessionLocal,
    init_db,
    CropProfileModel,
    SoilProfileModel,
    LocationPredictionRecord
)
from schemas import (
    UniversalIngestionRequest,
    UniversalPredictionResponse,
    ThermodynamicDiagnostics,
    EvapotranspirationDepths,
    CropWaterFootprintOutput,
    TimePeriodDiagnostics,
    SimplifiedScenarioPredictionRequest,
    ThreeWayScenarioResponse
)
from normalization_engine import PhysicalNormalizationEngine
from universal_engine import UniversalCropWaterFootprintEngine
from climatology_engine import ClimatologyScenarioEngine

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema and baseline data on startup."""
    init_db()
    yield

# ==============================================================================
# FastAPI Application Initialization & Middleware
# ==============================================================================
app = FastAPI(
    title="AquaCrop AI — Universal Crop Water Footprint Engine API",
    description="High-precision location-agnostic API for predicting Green, Blue, and Total Crop Water Footprints (m³/ton) using Physics-Informed ML and FAO-56 thermodynamics.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for external client applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instances
engine_instance = UniversalCropWaterFootprintEngine()
scenario_engine = ClimatologyScenarioEngine()

# ==============================================================================
# Database Session Dependency Injection
# ==============================================================================
def get_db():
    """
    Dependency generator that opens a fresh SQLAlchemy session for every
    incoming HTTP request and guarantees clean closure afterward.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================================================================
# Additional Pydantic Schemas for API Management
# ==============================================================================
class CropProfileCreate(BaseModel):
    crop_key: str = Field(..., description="Unique alphanumeric identifier (e.g., 'quinoa', 'olive')")
    name: str = Field(..., description="Human-readable crop name")
    kc_ini: float = Field(0.35, description="Initial stage crop coefficient Kc")
    kc_mid: float = Field(1.15, description="Mid-season peak crop coefficient Kc")
    kc_end: float = Field(0.50, description="Late stage harvest crop coefficient Kc")
    kc_avg: float = Field(0.85, description="Season-average crop coefficient Kc")
    yield_baseline_ton_ha: float = Field(..., description="Typical regional economic harvest yield in ton/ha")
    root_depth_m: float = Field(1.0, description="Effective rooting depth in meters")
    depletion_fraction_p: float = Field(0.5, description="Soil water depletion fraction for no stress (0-1)")

class CropProfileOut(BaseModel):
    crop_key: str
    name: str
    kc_ini: float
    kc_mid: float
    kc_end: float
    kc_avg: float
    yield_baseline_ton_ha: float
    root_depth_m: float
    depletion_fraction_p: float

    model_config = ConfigDict(from_attributes=True)

class SoilProfileOut(BaseModel):
    soil_key: str
    name: str
    field_capacity_fc: float
    wilting_point_wp: float
    infiltration_alpha: float
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class PredictionRecordOut(BaseModel):
    id: int
    location_label: str
    latitude_deg: float
    elevation_m: float
    crop_key: str
    soil_key: str
    actual_et_mm: float
    green_cwf_m3_ton: float
    blue_cwf_m3_ton: float
    total_cwf_m3_ton: float

    model_config = ConfigDict(from_attributes=True)

# ==============================================================================
# API Endpoints
# ==============================================================================

@app.get("/health", tags=["System Diagnostics"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint confirming API status and database connectivity."""
    try:
        soil_count = db.query(SoilProfileModel).count()
        crop_count = db.query(CropProfileModel).count()
        return {
            "status": "healthy",
            "service": "AquaCrop AI Universal Engine",
            "database": "connected",
            "registered_crops": crop_count,
            "registered_soils": soil_count,
            "ml_model_loaded": engine_instance.model is not None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {e}"
        )

@app.post("/api/v1/cwf/predict", response_model=UniversalPredictionResponse, tags=["CWF Prediction Engine"])
def predict_crop_water_footprint(
    request: UniversalIngestionRequest,
    db: Session = Depends(get_db)
):
    """
    Main Universal Prediction Gateway.
    
    Accepts full 4-pillar payload (Atmospheric, Soil, Crop, Agronomy), performs
    dimensionless physics normalization, queries dynamic database profiles, runs
    LightGBM/FAO-56 inference, logs audit records, and returns full CWF diagnostics.
    """
    # 1. Fetch Crop & Soil Database Records
    crop_prof = db.query(CropProfileModel).filter_by(crop_key=request.crop.crop_type.lower()).first()
    if not crop_prof:
        crop_prof = db.query(CropProfileModel).filter_by(crop_key='sugarcane').first()
        if not crop_prof:
            raise HTTPException(status_code=404, detail="Default crop profile not found in database.")

    soil_prof = db.query(SoilProfileModel).filter_by(soil_key=request.soil.soil_type.lower()).first()
    if not soil_prof:
        soil_prof = db.query(SoilProfileModel).filter_by(soil_key='loam').first()
        if not soil_prof:
            raise HTTPException(status_code=404, detail="Default soil profile not found in database.")

    # 2. Extract Effective Coefficients
    kc_map = {
        'initial': crop_prof.kc_ini,
        'mid': crop_prof.kc_mid,
        'end': crop_prof.kc_end,
        'average': crop_prof.kc_avg
    }
    kc = request.crop.custom_kc if request.crop.custom_kc is not None else kc_map.get(request.crop.growth_stage, crop_prof.kc_avg)
    crop_yield = request.crop.custom_yield_ton_ha if request.crop.custom_yield_ton_ha is not None else crop_prof.yield_baseline_ton_ha
    alpha = request.soil.custom_infiltration_alpha if request.soil.custom_infiltration_alpha is not None else soil_prof.infiltration_alpha
    fc = request.soil.custom_field_capacity if request.soil.custom_field_capacity is not None else soil_prof.field_capacity_fc
    wp = request.soil.custom_wilting_point if request.soil.custom_wilting_point is not None else soil_prof.wilting_point_wp

    # 3. Decoupled Physical Normalization
    atm = request.atmosphere
    norm = PhysicalNormalizationEngine()
    vpd = norm.vapor_pressure_deficit(atm.temp_c, atm.rh_pct)
    ssi = norm.soil_water_stress_index(request.soil.volumetric_moisture, fc, wp)
    r_a = norm.extraterrestrial_radiation(atm.latitude_deg, atm.day_of_year)
    rel_solar = norm.relative_solar_forcing(atm.solar_rad_mj, atm.latitude_deg, atm.day_of_year)
    et0_pm = norm.reference_et0_penman_monteith(atm.temp_c, atm.solar_rad_mj, atm.rh_pct, atm.wind_speed_ms, atm.elevation_m)

    # 4. Actual ET Calculation with Time Period Scope
    raw_calc = engine_instance.analyze_location(
        temp_c=atm.temp_c,
        solar_rad_mj=atm.solar_rad_mj,
        precip_mm=atm.precip_mm,
        soil_moisture=request.soil.volumetric_moisture,
        rh_pct=atm.rh_pct,
        wind_speed_ms=atm.wind_speed_ms,
        elevation_m=atm.elevation_m,
        latitude_deg=atm.latitude_deg,
        day_of_year=atm.day_of_year,
        crop_type=crop_prof.crop_key,
        soil_type=soil_prof.soil_key,
        custom_kc=kc,
        custom_yield_ton_ha=crop_yield,
        custom_alpha=alpha,
        hour_of_day=atm.hour_of_day,
        growth_stage=request.crop.growth_stage,
        custom_fc=fc,
        custom_wp=wp,
        time_period=request.time_period
    )

    actual_et_mm = raw_calc['evapotranspiration_depth_mm']['actual_et_mm']
    gwf = raw_calc['crop_water_footprint_m3_ton']['green_water_footprint_m3_ton']
    bwf = raw_calc['crop_water_footprint_m3_ton']['blue_water_footprint_m3_ton']
    twf = raw_calc['crop_water_footprint_m3_ton']['total_water_footprint_m3_ton']

    # 5. Thread-Safe Audit Logging via Injected DB Session
    try:
        audit_record = LocationPredictionRecord(
            location_label=request.location_label or "API Client",
            latitude_deg=atm.latitude_deg,
            elevation_m=atm.elevation_m,
            crop_key=crop_prof.crop_key,
            soil_key=soil_prof.soil_key,
            temp_c=atm.temp_c,
            solar_rad_mj=atm.solar_rad_mj,
            precip_mm=atm.precip_mm,
            soil_moisture=request.soil.volumetric_moisture,
            actual_et_mm=actual_et_mm,
            green_cwf_m3_ton=gwf,
            blue_cwf_m3_ton=bwf,
            total_cwf_m3_ton=twf
        )
        db.add(audit_record)
        db.commit()
    except Exception as err:
        db.rollback()
        print(f"[API] Audit logging notice: {err}")

    return UniversalPredictionResponse(
        status="success",
        location_label=request.location_label or "Custom Region",
        crop_name=crop_prof.name,
        soil_type=soil_prof.name,
        thermodynamic_diagnostics=ThermodynamicDiagnostics(**raw_calc['thermodynamic_diagnostics']),
        evapotranspiration_depths_mm=EvapotranspirationDepths(**raw_calc['evapotranspiration_depth_mm']),
        crop_water_footprint_m3_ton=CropWaterFootprintOutput(**raw_calc['crop_water_footprint_m3_ton']),
        time_period_summary=TimePeriodDiagnostics(**raw_calc['time_period_summary']),
        irrigation_stress_assessment=raw_calc['irrigation_stress_assessment']
    )

@app.post("/api/v1/cwf/scenario-predict", response_model=ThreeWayScenarioResponse, tags=["CWF Zero-Friction Scenario Engine"])
def predict_three_way_scenario(request: SimplifiedScenarioPredictionRequest):
    """
    Zero-Friction Scenario Prediction Gateway (Brainstorm Architecture).
    
    Accepts ONLY: Location, Crop Type, and Time Horizon (1 day to 10 years).
    Queries the 25-Year Empirical Climatology Database (2000-2025) and generates
    the 3-Way Quantile Forecast Triad (Normal, Drought, Flood) along with
    the Empirical Probability Meter and Multi-Hazard Risk Indicators.
    """
    return scenario_engine.predict_scenario_triad(
        location=request.location,
        crop_type=request.crop_type,
        time_horizon=request.time_horizon,
        enso_phase=getattr(request, 'enso_phase', 'neutral') or 'neutral',
        rare_event=request.rare_event,
        irrigation_access_fraction=request.irrigation_access_fraction,
        yield_disruption_fraction=request.yield_disruption_fraction,
        event_evidence_note=request.event_evidence_note,
    )


@app.get("/api/v1/crops", response_model=List[CropProfileOut], tags=["Crop & Soil Profiles"])
def list_crops(db: Session = Depends(get_db)):
    """Fetches all registered crop profiles from the database."""
    return db.query(CropProfileModel).all()

@app.post("/api/v1/crops", response_model=CropProfileOut, status_code=status.HTTP_201_CREATED, tags=["Crop & Soil Profiles"])
def register_crop(crop_in: CropProfileCreate, db: Session = Depends(get_db)):
    """Dynamically registers or updates a custom regional crop profile in the database."""
    existing = db.query(CropProfileModel).filter_by(crop_key=crop_in.crop_key.lower()).first()
    if existing:
        for attr, val in crop_in.dict().items():
            setattr(existing, attr, val)
        db.commit()
        db.refresh(existing)
        return existing
    
    new_crop = CropProfileModel(**crop_in.dict())
    db.add(new_crop)
    db.commit()
    db.refresh(new_crop)
    return new_crop

@app.get("/api/v1/soils", response_model=List[SoilProfileOut], tags=["Crop & Soil Profiles"])
def list_soils(db: Session = Depends(get_db)):
    """Fetches all registered hydraulic soil profiles from the database."""
    return db.query(SoilProfileModel).all()

@app.get("/api/v1/records", response_model=List[PredictionRecordOut], tags=["Audit Logs"])
def list_recent_predictions(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieves recent calculation audit records committed to the database."""
    return db.query(LocationPredictionRecord).order_by(LocationPredictionRecord.id.desc()).limit(limit).all()

# ==============================================================================
# Autonomous Model Self-Training & Hyperparameter Optimization Endpoints
# ==============================================================================
@app.post("/api/v1/model/retrain", tags=["Autonomous Self-Training"])
def trigger_adaptive_retraining(n_iter: int = 15, cv_folds: int = 3):
    """
    Autonomously unlocks hyperparameters, executes cross-validation search over
    the updated master dataset, promotes the optimal model, and hot-reloads it in memory.
    """
    from adaptive_trainer import AdaptiveModelTrainer
    trainer = AdaptiveModelTrainer()
    try:
        results = trainer.optimize_and_train(n_iter_search=n_iter, cv_folds=cv_folds, auto_promote=True)
        # Hot-reload in memory
        engine_instance.reload_model()
        return {
            "status": "success",
            "message": "Model autonomously retrained and hot-reloaded into active memory.",
            "metrics": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autonomous retraining failed: {str(e)}")

@app.get("/api/v1/model/status", tags=["Autonomous Self-Training"])
def get_active_model_status():
    """Returns active LightGBM production model metadata, hyperparameters, and R² score."""
    from adaptive_trainer import AdaptiveModelTrainer
    trainer = AdaptiveModelTrainer()
    metadata = trainer.get_latest_model_status()
    metadata["engine_model_loaded"] = engine_instance.model is not None
    return metadata

if __name__ == "__main__":
    import uvicorn
    print("================================================================")
    print(" Starting AquaCrop AI FastAPI Gateway on http://127.0.0.1:8000")
    print(" Interactive Documentation available at http://127.0.0.1:8000/docs")
    print("================================================================")
    uvicorn.run(app, host="127.0.0.1", port=8000)
