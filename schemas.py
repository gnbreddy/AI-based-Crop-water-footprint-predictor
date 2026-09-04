from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

# ==============================================================================
# Pillar 1: Atmospheric & Energy Demand Payload
# ==============================================================================
class AtmosphericPayload(BaseModel):
    temp_c: float = Field(..., description="2m Air temperature in degrees Celsius", ge=-50.0, le=65.0)
    solar_rad_mj: float = Field(..., description="Surface downward solar radiation in MJ/m^2", ge=0.0, le=50.0)
    rh_pct: float = Field(60.0, description="Relative humidity percentage", ge=0.0, le=100.0)
    wind_speed_ms: float = Field(3.0, description="Wind speed at 2m height in m/s", ge=0.0, le=60.0)
    precip_mm: float = Field(0.0, description="Gross precipitation depth in mm", ge=0.0, le=1000.0)
    elevation_m: float = Field(100.0, description="Altitude above sea level in meters", ge=-500.0, le=9000.0)
    latitude_deg: float = Field(16.0, description="Geographic latitude in decimal degrees", ge=-90.0, le=90.0)
    day_of_year: int = Field(180, description="Calendar day of year (1-365)", ge=1, le=366)
    hour_of_day: int = Field(12, description="Hour of the day in UTC/local (0-23)", ge=0, le=23)

# ==============================================================================
# Pillar 2: Soil Matrix & Hydrological Supply Payload
# ==============================================================================
class SoilPayload(BaseModel):
    soil_type: str = Field('loam', description="Standard soil texture class key (e.g., loam, clay, sandy_loam)")
    volumetric_moisture: float = Field(..., description="Root-zone volumetric soil moisture in m^3/m^3", ge=0.0, le=0.9)
    custom_field_capacity: Optional[float] = Field(None, description="Custom Field Capacity (FC) in m^3/m^3", ge=0.05, le=0.60)
    custom_wilting_point: Optional[float] = Field(None, description="Custom Permanent Wilting Point (WP) in m^3/m^3", ge=0.01, le=0.40)
    custom_infiltration_alpha: Optional[float] = Field(None, description="Custom effective rainfall infiltration factor (0-1)", ge=0.1, le=1.0)

# ==============================================================================
# Pillar 3 & 4: Crop Phenology & Agronomic Output Payload
# ==============================================================================
class CropPayload(BaseModel):
    crop_type: str = Field('sugarcane', description="Crop species identifier (e.g., sugarcane, cotton, wheat, rice)")
    growth_stage: Literal['initial', 'mid', 'end', 'average'] = Field('average', description="Crop developmental growth stage")
    custom_kc: Optional[float] = Field(None, description="Custom crop coefficient factor", ge=0.1, le=2.5)
    custom_yield_ton_ha: Optional[float] = Field(None, description="Regional economic harvest yield in ton/ha", ge=0.1, le=500.0)
    custom_root_depth_m: Optional[float] = Field(None, description="Effective root-zone depth in meters", ge=0.1, le=5.0)

# ==============================================================================
# Pillar 5: Prediction Time Period & Horizon Payload
# ==============================================================================
class TimePeriodPayload(BaseModel):
    mode: Literal['instantaneous', 'growing_season', 'annual', 'future_horizon'] = Field(
        'growing_season',
        description="Temporal scope for water footprint evaluation: instantaneous (6h), growing_season, annual (365d), or future_horizon (multi-year projection)"
    )
    duration_days: Optional[float] = Field(None, description="Custom duration in days for seasonal/growing period", ge=1.0, le=3650.0)
    target_horizon_year: Optional[int] = Field(2030, description="Target climate projection horizon year (e.g., 2030, 2040, 2050)", ge=2024, le=2100)
    start_year: Optional[int] = Field(2026, description="Start year for future projection horizon", ge=1990, le=2050)

# ==============================================================================
# Unified Ingestion Request Payload
# ==============================================================================
class UniversalIngestionRequest(BaseModel):
    location_label: Optional[str] = Field("Custom Location", description="Descriptive name or coordinate label for the region")
    atmosphere: AtmosphericPayload
    soil: SoilPayload
    crop: CropPayload
    time_period: Optional[TimePeriodPayload] = Field(default_factory=TimePeriodPayload)

# ==============================================================================
# Standardized Universal Diagnostics Response Schema
# ==============================================================================
class ThermodynamicDiagnostics(BaseModel):
    vapor_pressure_deficit_kpa: float
    soil_stress_index_0_1: float
    extraterrestrial_radiation_mj: float
    relative_solar_forcing: float
    fao56_reference_et0_mm: float

class EvapotranspirationDepths(BaseModel):
    actual_et_mm: float
    crop_adjusted_et_mm: float
    effective_precipitation_mm: float
    green_evapotranspiration_mm: float
    blue_evapotranspiration_mm: float

class CropWaterFootprintOutput(BaseModel):
    green_water_footprint_m3_ton: float
    blue_water_footprint_m3_ton: float
    total_water_footprint_m3_ton: float
    green_share_pct: float
    blue_share_pct: float

class TimePeriodDiagnostics(BaseModel):
    mode: str
    duration_days: float
    target_horizon_year: Optional[int] = None
    scaling_factor: float
    total_period_crop_water_use_m3_ha: float
    description: str

class UniversalPredictionResponse(BaseModel):
    status: str = "success"
    location_label: str
    crop_name: str
    soil_type: str
    thermodynamic_diagnostics: ThermodynamicDiagnostics
    evapotranspiration_depths_mm: EvapotranspirationDepths
    crop_water_footprint_m3_ton: CropWaterFootprintOutput
    time_period_summary: Optional[TimePeriodDiagnostics] = None
    irrigation_stress_assessment: str

# ==============================================================================
# Simplified Zero-Friction Scenario Request & 3-Way Triad Response
# ==============================================================================
class SimplifiedScenarioPredictionRequest(BaseModel):
    location: str = Field('kolhapur', description="Location/Taluka key (e.g. kolhapur, karveer, shirol, radhanagari, kagal, hatkanangale) or custom coordinate")
    crop_type: str = Field('sugarcane', description="Crop species: sugarcane, cotton, wheat, rice")
    time_horizon: str = Field(
        '1_year',
        description="Horizon: 1_day, 2_days, 3_days, 7_days, 2_weeks, 1_month, 3_months, 6_months, 1_year, 2_years, 3_years, 5_years, 10_years"
    )
    enso_phase: Optional[str] = Field('neutral', description="Macro-climate phase: neutral, el_nino (drought risk), la_nina (heavy monsoon)")
    latitude: Optional[float] = Field(None, description="Optional custom latitude coordinate")
    longitude: Optional[float] = Field(None, description="Optional custom longitude coordinate")
    rare_event: Literal['none', 'pandemic_disruption'] = Field(
        'none',
        description="Optional non-climatic disruption scenario. Pandemic disruption is never inferred from weather or a year alone."
    )
    irrigation_access_fraction: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Evidence-backed fraction of normal irrigation access during a disruption; omitted means no supply reduction is assumed."
    )
    yield_disruption_fraction: Optional[float] = Field(
        None, ge=0.0, le=0.90,
        description="Evidence-backed fraction of normal yield lost due to a non-climatic disruption; omitted means no yield effect is assumed."
    )
    event_evidence_note: Optional[str] = Field(
        None, max_length=500,
        description="Optional source or field-observation note. It is returned for auditability and is not treated as model training data."
    )

class ScenarioMetrics(BaseModel):
    scenario_label: str
    cwf_green_m3_ton: float
    cwf_blue_m3_ton: float
    cwf_total_m3_ton: float
    green_share_pct: float
    blue_share_pct: float
    period_etc_mm: float
    period_precip_mm: float
    actual_yield_ton_ha: float
    yield_loss_pct: float
    yield_loss_ton_ha: Optional[float] = 0.0
    revenue_loss_inr_ha: Optional[float] = 0.0
    kcb_transpiration: Optional[float] = None
    ke_soil_evaporation: Optional[float] = None
    effective_kc: Optional[float] = None
    stomatal_attenuation_factor: Optional[float] = None
    capillary_upflux_mm: Optional[float] = 0.0
    vpd_kpa: float
    soil_moisture_root: float

class HazardAssessment(BaseModel):
    drought_hazard_index_pct: int
    flood_waterlogging_risk: str
    irrigation_urgency: str
    days_until_moisture_stress: int
    blue_water_demand_surge_pct: Optional[float] = 0.0
    actionable_advisory: str
    marathi_advisory: Optional[str] = None

class ThreeWayScenarioResponse(BaseModel):
    status: str = "success"
    query_context: dict
    biophysical_diagnostics: Optional[dict] = None
    probability_distribution: dict
    scenarios: dict
    hazard_assessment: dict
    rare_event_assessment: Optional[dict] = None
    # Cumulative, seasonally shaped green/blue trajectories used by the web chart.
    # Kept as a dictionary so the API remains forward-compatible with new scenarios.
    seasonal_trajectory: Optional[dict] = None
