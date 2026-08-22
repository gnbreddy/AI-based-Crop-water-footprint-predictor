import numpy as np
import pandas as pd
from scipy.optimize import minimize
from config import DEFAULT_CWF_PARAMS

class CropWaterFootprintCalibrator:
    """
    Computes and calibrates Crop Water Footprint (CWF) components:
    - Green Water Footprint (GWF): Rainwater consumed (m3/ton)
    - Blue Water Footprint (BWF): Irrigation/surface/groundwater consumed (m3/ton)
    - Total Water Footprint (TWF): GWF + BWF (m3/ton)
    
    Based on the standard FAO-56 & Water Footprint Network (WFN) methodology:
        ET_c = Kc * ET_pred
        P_eff = alpha * Precip
        ET_green = min(ET_c, P_eff)
        ET_blue = max(0, ET_c - P_eff)
        GWF = (10 * sum(ET_green)) / Yield
        BWF = (10 * sum(ET_blue)) / Yield
    """

    def __init__(self, params=None):
        self.params = DEFAULT_CWF_PARAMS.copy()
        if params:
            self.params.update(params)

    def compute_footprint(self, et_series, precip_series, params=None, annualize=True):
        """
        Computes 6-hourly and cumulative Green, Blue, and Total Water Footprint.
        
        Args:
            et_series (np.ndarray or pd.Series): Evapotranspiration (mm)
            precip_series (np.ndarray or pd.Series): Precipitation (mm)
            params (dict, optional): Custom physical coefficients.
            annualize (bool): If True, normalizes multi-year time series to annual average (4 steps/day).
            
        Returns:
            dict: Timeseries and aggregated metrics for GWF, BWF, and TWF.
        """
        p = self.params if params is None else {**self.params, **params}
        
        kc = p['crop_coefficient_kc']
        alpha = p['effective_precip_factor']
        yield_val = p['yield_baseline']
        factor = p['water_conversion_factor']

        et = np.asarray(et_series, dtype=float)
        precip = np.asarray(precip_series, dtype=float)

        # Crop-adjusted ET
        et_c = np.maximum(0, kc * et)
        
        # Effective precipitation
        p_eff = np.maximum(0, alpha * precip)

        # Partitioning Green and Blue components
        et_green = np.minimum(et_c, p_eff)
        et_blue = np.maximum(0, et_c - p_eff)

        # Time normalization factor (4 timesteps per day = 1461 steps/year)
        years_span = max(1.0, len(et) / (365.25 * 4)) if annualize else 1.0

        # Annualized Crop Water Use (m3/ha/year)
        cwu_green = factor * (np.sum(et_green) / years_span)
        cwu_blue = factor * (np.sum(et_blue) / years_span)
        cwu_total = cwu_green + cwu_blue

        # Crop Water Footprint (m3/ton)
        gwf = cwu_green / yield_val if yield_val > 0 else 0.0
        bwf = cwu_blue / yield_val if yield_val > 0 else 0.0
        twf = gwf + bwf

        return {
            'et_c_series': et_c,
            'p_eff_series': p_eff,
            'et_green_series': et_green,
            'et_blue_series': et_blue,
            'total_et_mm_annual': float(np.sum(et_c) / years_span),
            'cwu_green_m3_ha': float(cwu_green),
            'cwu_blue_m3_ha': float(cwu_blue),
            'cwu_total_m3_ha': float(cwu_total),
            'green_water_footprint_m3_ton': float(gwf),
            'blue_water_footprint_m3_ton': float(bwf),
            'total_water_footprint_m3_ton': float(twf),
            'years_span': float(years_span),
            'parameters_used': p
        }

    def calibrate_coefficients(self, et_series, precip_series, target_twf, target_gwf_ratio=0.70, annualize=True):
        """
        Optimizes empirical coefficients (Kc, alpha, yield baseline) to align predictions
        with regional benchmarks or ground truth hydrological observations.
        
        Args:
            et_series: Predicted/actual ET series
            precip_series: Precipitation series
            target_twf: Target total water footprint benchmark (m3/ton)
            target_gwf_ratio: Target fraction of green water footprint (e.g., 0.70 for 70% green)
            annualize: Whether to normalize time series to annual rates
            
        Returns:
            dict: Optimized parameters and calibrated evaluation metrics.
        """
        print(f"[Calibrator] Calibrating coefficients for Target TWF = {target_twf:.1f} m³/ton (Green Ratio: {target_gwf_ratio*100:.0f}%)...")
        
        def loss_fn(weights):
            kc, alpha, yield_val = weights
            test_p = {
                'crop_coefficient_kc': kc,
                'effective_precip_factor': alpha,
                'yield_baseline': yield_val,
                'water_conversion_factor': 10.0
            }
            res = self.compute_footprint(et_series, precip_series, params=test_p, annualize=annualize)
            
            twf_error = (res['total_water_footprint_m3_ton'] - target_twf) ** 2
            green_ratio = res['green_water_footprint_m3_ton'] / (res['total_water_footprint_m3_ton'] + 1e-6)
            ratio_error = (green_ratio - target_gwf_ratio) ** 2
            
            return twf_error + 100.0 * ratio_error

        # Initial guess: [Kc, alpha, yield]
        initial_guess = [
            self.params['crop_coefficient_kc'],
            self.params['effective_precip_factor'],
            self.params['yield_baseline']
        ]
        
        bounds = [
            (0.5, 1.6),     # Kc range
            (0.4, 0.95),    # alpha range
            (20.0, 150.0)   # Yield range (ton/ha)
        ]

        opt_result = minimize(loss_fn, initial_guess, bounds=bounds, method='L-BFGS-B')

        best_kc, best_alpha, best_yield = opt_result.x
        optimized_params = {
            'crop_coefficient_kc': float(best_kc),
            'effective_precip_factor': float(best_alpha),
            'yield_baseline': float(best_yield),
            'water_conversion_factor': 10.0
        }
        
        self.params = optimized_params
        calibrated_footprint = self.compute_footprint(et_series, precip_series, optimized_params)
        
        print(f"[Calibrator] Optimization Converged: Kc={best_kc:.3f}, alpha={best_alpha:.3f}, Yield={best_yield:.2f} ton/ha")
        print(f"[Calibrator] Calibrated TWF: {calibrated_footprint['total_water_footprint_m3_ton']:.2f} m³/ton (GWF: {calibrated_footprint['green_water_footprint_m3_ton']:.2f}, BWF: {calibrated_footprint['blue_water_footprint_m3_ton']:.2f})")

        return {
            'optimized_params': optimized_params,
            'calibrated_footprint': calibrated_footprint,
            'optimization_success': opt_result.success
        }
