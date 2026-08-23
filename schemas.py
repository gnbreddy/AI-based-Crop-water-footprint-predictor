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
# Unified Ingestion Request Payload
# ==============================================================================
class UniversalIngestionRequest(BaseModel):
    location_label: Optional[str] = Field("Custom Location", description="Descriptive name or coordinate label for the region")
    atmosphere: AtmosphericPayload
    soil: SoilPayload
    crop: CropPayload

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

class UniversalPredictionResponse(BaseModel):
    status: str = "success"
    location_label: str
    crop_name: str
    soil_type: str
    thermodynamic_diagnostics: ThermodynamicDiagnostics
    evapotranspiration_depths_mm: EvapotranspirationDepths
    crop_water_footprint_m3_ton: CropWaterFootprintOutput
    irrigation_stress_assessment: str
