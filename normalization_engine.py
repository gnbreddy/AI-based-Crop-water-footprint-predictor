import numpy as np

class PhysicalNormalizationEngine:
    """
    Decoupled Physical Normalization Engine.
    
    Transforms raw atmospheric, soil, and geospatial inputs into dimensionless
    thermodynamic invariants and universal hydrological ratios.
    """

    @staticmethod
    def saturation_vapor_pressure(temp_c: float) -> float:
        """
        Computes saturation vapor pressure e_s (kPa) via Tetens equation.
        e_s(T) = 0.6108 * exp((17.27 * T) / (T + 237.3))
        """
        return float(0.6108 * np.exp((17.27 * temp_c) / (temp_c + 237.3)))

    @staticmethod
    def vapor_pressure_deficit(temp_c: float, rh_pct: float) -> float:
        """
        Computes Vapor Pressure Deficit VPD = e_s - e_a (kPa).
        Quantifies atmospheric dryness / moisture pulling force.
        """
        e_s = PhysicalNormalizationEngine.saturation_vapor_pressure(temp_c)
        e_a = e_s * (np.clip(rh_pct, 0.0, 100.0) / 100.0)
        return float(max(0.0, e_s - e_a))

    @staticmethod
    def slope_vapor_pressure_curve(temp_c: float) -> float:
        """
        Computes the slope of the saturation vapor pressure curve Delta (kPa/°C).
        Delta = (4098 * e_s) / (T + 237.3)^2
        """
        e_s = PhysicalNormalizationEngine.saturation_vapor_pressure(temp_c)
        return float((4098.0 * e_s) / np.power(temp_c + 237.3, 2))

    @staticmethod
    def psychrometric_constant(elevation_m: float) -> float:
        """
        Computes psychrometric constant gamma (kPa/°C) corrected for altitude.
        P_atm = 101.3 * ((293 - 0.0065 * z) / 293)^5.26
        gamma = 0.000665 * P_atm
        """
        p_atm = 101.3 * np.power((293.0 - 0.0065 * elevation_m) / 293.0, 5.26)
        return float(0.000665 * p_atm)

    @staticmethod
    def extraterrestrial_radiation(latitude_deg: float, day_of_year: int) -> float:
        """
        Computes extraterrestrial solar radiation R_a (MJ/m^2/day).
        Accounts for solar declination, latitude, and daylight hours.
        """
        phi = np.radians(latitude_deg)
        dr = 1.0 + 0.033 * np.cos(2.0 * np.pi * day_of_year / 365.0)
        delta = 0.409 * np.sin((2.0 * np.pi * day_of_year / 365.0) - 1.39)
        
        arg = -np.tan(phi) * np.tan(delta)
        arg = np.clip(arg, -1.0, 1.0)
        ws = np.arccos(arg)
        
        g_sc = 0.0820  # Solar constant MJ/m^2/min
        r_a = (24.0 * 60.0 / np.pi) * g_sc * dr * (
            ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws)
        )
        return float(max(0.1, r_a))

    @staticmethod
    def relative_solar_forcing(solar_rad_mj: float, latitude_deg: float, day_of_year: int) -> float:
        """
        Dimensionless ratio of downward solar radiation to extraterrestrial potential (R_s / R_a).
        """
        r_a = PhysicalNormalizationEngine.extraterrestrial_radiation(latitude_deg, day_of_year)
        return float(solar_rad_mj / (r_a + 1e-6))

    @staticmethod
    def soil_water_stress_index(volumetric_moisture: float, field_capacity: float, wilting_point: float) -> float:
        """
        Dimensionless Soil Water Stress Index SSI in range [0.0, 1.0].
        0.0 = Permanent Wilting Point (complete water deficit).
        1.0 = Field Capacity (saturated root zone).
        """
        ssi = (volumetric_moisture - wilting_point) / (field_capacity - wilting_point + 1e-6)
        return float(np.clip(ssi, 0.0, 1.0))

    @staticmethod
    def reference_et0_penman_monteith(temp_c: float, 
                                      solar_rad_mj: float, 
                                      rh_pct: float, 
                                      wind_speed_ms: float, 
                                      elevation_m: float = 100.0) -> float:
        """
        Standardized FAO-56 Penman-Monteith Reference Evapotranspiration ET_0 (mm).
        """
        delta = PhysicalNormalizationEngine.slope_vapor_pressure_curve(temp_c)
        gamma = PhysicalNormalizationEngine.psychrometric_constant(elevation_m)
        vpd = PhysicalNormalizationEngine.vapor_pressure_deficit(temp_c, rh_pct)
        
        # Net radiation R_n approximation ~ 0.77 * R_s
        r_n = 0.77 * solar_rad_mj

        numerator = 0.408 * delta * r_n + gamma * (900.0 / (temp_c + 273.0)) * wind_speed_ms * vpd
        denominator = delta + gamma * (1.0 + 0.34 * wind_speed_ms)
        return float(max(0.02, numerator / (denominator + 1e-6)))
