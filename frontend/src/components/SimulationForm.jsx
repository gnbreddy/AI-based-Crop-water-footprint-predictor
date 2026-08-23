import React, { useState, useEffect } from 'react';
import { Sliders, Play, Sparkles, MapPin, Layers, Sun } from 'lucide-react';
import { fetchCrops, fetchSoils } from '../api/cwfApi';

const PRESETS = [
  {
    name: 'Kolhapur Sugarcane',
    label: 'Kolhapur Farm Block-A',
    temp_c: 28.5,
    solar_rad_mj: 21.0,
    rh_pct: 65.0,
    wind_speed_ms: 2.8,
    precip_mm: 5.0,
    elevation_m: 570.0,
    latitude_deg: 16.7,
    longitude_deg: 74.2,
    soil_type: 'clay_loam',
    volumetric_moisture: 0.28,
    crop_type: 'sugarcane',
    growth_stage: 'mid',
    custom_yield_ton_ha: 150.0
  },
  {
    name: 'Nile Delta Cotton',
    label: 'Nile Delta Irrigation Node',
    temp_c: 36.0,
    solar_rad_mj: 25.0,
    rh_pct: 30.0,
    wind_speed_ms: 4.0,
    precip_mm: 0.0,
    elevation_m: 15.0,
    latitude_deg: 30.5,
    longitude_deg: 31.0,
    soil_type: 'sandy_loam',
    volumetric_moisture: 0.12,
    crop_type: 'cotton',
    growth_stage: 'mid',
    custom_yield_ton_ha: 3.5
  },
  {
    name: 'Kansas Wheat',
    label: 'Kansas Plains Field #4',
    temp_c: 19.5,
    solar_rad_mj: 19.0,
    rh_pct: 55.0,
    wind_speed_ms: 3.5,
    precip_mm: 12.0,
    elevation_m: 250.0,
    latitude_deg: 38.5,
    longitude_deg: -98.0,
    soil_type: 'silt_loam',
    volumetric_moisture: 0.24,
    crop_type: 'wheat',
    growth_stage: 'mid',
    custom_yield_ton_ha: 5.0
  },
  {
    name: 'Mekong Monsoon Rice',
    label: 'Mekong Delta Paddy Node',
    temp_c: 29.0,
    solar_rad_mj: 16.5,
    rh_pct: 85.0,
    wind_speed_ms: 2.0,
    precip_mm: 45.0,
    elevation_m: 10.0,
    latitude_deg: 10.2,
    longitude_deg: 105.8,
    soil_type: 'clay',
    volumetric_moisture: 0.36,
    crop_type: 'rice',
    growth_stage: 'mid',
    custom_yield_ton_ha: 4.5
  }
];

export default function SimulationForm({ onPredict, loading, onCoordsChange }) {
  const [crops, setCrops] = useState([]);
  const [soils, setSoils] = useState([]);

  const [formData, setFormData] = useState({
    location_label: 'Kolhapur Farm Block-A',
    latitude_deg: 16.7,
    longitude_deg: 74.2,
    elevation_m: 570.0,
    temp_c: 28.5,
    solar_rad_mj: 21.0,
    rh_pct: 65.0,
    wind_speed_ms: 2.8,
    precip_mm: 5.0,
    day_of_year: 180,
    hour_of_day: 12,
    soil_type: 'clay_loam',
    volumetric_moisture: 0.28,
    crop_type: 'sugarcane',
    growth_stage: 'mid',
    custom_yield_ton_ha: 150.0,
  });

  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const [cropsData, soilsData] = await Promise.all([fetchCrops(), fetchSoils()]);
        setCrops(cropsData);
        setSoils(soilsData);
      } catch (err) {
        console.error('Failed to load metadata', err);
      }
    };
    loadMetadata();
  }, []);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    const val = type === 'number' ? parseFloat(value) : value;
    setFormData((prev) => {
      const updated = { ...prev, [name]: val };
      if ((name === 'latitude_deg' || name === 'longitude_deg') && onCoordsChange) {
        onCoordsChange(updated.latitude_deg, updated.longitude_deg, updated.location_label);
      }
      return updated;
    });
  };

  const applyPreset = (preset) => {
    setFormData((prev) => ({ ...prev, ...preset }));
    if (onCoordsChange) {
      onCoordsChange(preset.latitude_deg, preset.longitude_deg, preset.label);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      location_label: formData.location_label,
      atmosphere: {
        temp_c: formData.temp_c,
        solar_rad_mj: formData.solar_rad_mj,
        rh_pct: formData.rh_pct,
        wind_speed_ms: formData.wind_speed_ms,
        precip_mm: formData.precip_mm,
        elevation_m: formData.elevation_m,
        latitude_deg: formData.latitude_deg,
        day_of_year: formData.day_of_year,
        hour_of_day: formData.hour_of_day,
      },
      soil: {
        soil_type: formData.soil_type,
        volumetric_moisture: formData.volumetric_moisture,
      },
      crop: {
        crop_type: formData.crop_type,
        growth_stage: formData.growth_stage,
        custom_yield_ton_ha: formData.custom_yield_ton_ha,
      }
    };
    onPredict(payload);
  };

  // Get active crop details
  const activeCrop = crops.find((c) => c.crop_key === formData.crop_type);
  const activeSoil = soils.find((s) => s.soil_key === formData.soil_type);

  return (
    <form onSubmit={handleSubmit} className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-6 text-slate-200 shadow-xl space-y-5">
      {/* Header & Quick Presets */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-teal-500/10 text-teal-400 rounded-lg border border-teal-500/20">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Physical Simulation Controls</h2>
            <p className="text-[11px] text-slate-400">Configure atmospheric, soil hydraulic, and crop phenological pillars</p>
          </div>
        </div>

        {/* Preset Chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] uppercase font-bold text-slate-400 mr-1 flex items-center">
            <Sparkles className="w-3 h-3 mr-1 text-teal-400" /> Presets:
          </span>
          {PRESETS.map((p) => (
            <button
              key={p.name}
              type="button"
              onClick={() => applyPreset(p)}
              className="text-[11px] px-2.5 py-1 rounded-full bg-slate-800 hover:bg-teal-500/20 hover:text-teal-300 hover:border-teal-500/30 border border-slate-700 text-slate-300 transition-all"
            >
              {p.name}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs">
        {/* Pillar 1: Atmospheric */}
        <div className="space-y-3.5 bg-slate-800/40 p-4 rounded-xl border border-slate-800 shadow-inner">
          <div className="flex items-center space-x-1.5 border-b border-slate-700/50 pb-2">
            <Sun className="w-4 h-4 text-teal-400" />
            <span className="font-bold text-teal-400 uppercase tracking-wider text-[11px]">1. Atmospheric</span>
          </div>

          <div>
            <div className="flex justify-between text-slate-400 mb-1">
              <label>Temperature (T)</label>
              <span className="text-white font-mono">{formData.temp_c} °C</span>
            </div>
            <input type="range" min="-10" max="55" step="0.5" name="temp_c" value={formData.temp_c} onChange={handleChange} className="w-full accent-teal-400 bg-slate-950 h-1.5 rounded cursor-pointer" />
          </div>

          <div>
            <div className="flex justify-between text-slate-400 mb-1">
              <label>Solar Radiation (Rs)</label>
              <span className="text-white font-mono">{formData.solar_rad_mj} MJ/m²</span>
            </div>
            <input type="range" min="2" max="35" step="0.5" name="solar_rad_mj" value={formData.solar_rad_mj} onChange={handleChange} className="w-full accent-teal-400 bg-slate-950 h-1.5 rounded cursor-pointer" />
          </div>

          <div>
            <div className="flex justify-between text-slate-400 mb-1">
              <label>Relative Humidity (RH)</label>
              <span className="text-white font-mono">{formData.rh_pct} %</span>
            </div>
            <input type="range" min="5" max="100" step="1" name="rh_pct" value={formData.rh_pct} onChange={handleChange} className="w-full accent-teal-400 bg-slate-950 h-1.5 rounded cursor-pointer" />
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1">
            <div>
              <label className="block text-slate-400 mb-1">Wind (m/s)</label>
              <input type="number" step="0.1" name="wind_speed_ms" value={formData.wind_speed_ms} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white font-mono focus:border-teal-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Precip (mm)</label>
              <input type="number" step="0.5" name="precip_mm" value={formData.precip_mm} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white font-mono focus:border-teal-500 focus:outline-none" />
            </div>
          </div>
        </div>

        {/* Pillar 2: Soil Matrix */}
        <div className="space-y-3.5 bg-slate-800/40 p-4 rounded-xl border border-slate-800 shadow-inner">
          <div className="flex items-center space-x-1.5 border-b border-slate-700/50 pb-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <span className="font-bold text-emerald-400 uppercase tracking-wider text-[11px]">2. Soil Hydraulic</span>
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Soil Texture Matrix</label>
            <select name="soil_type" value={formData.soil_type} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white capitalize focus:border-emerald-500 focus:outline-none">
              {soils.map((s) => (
                <option key={s.soil_key} value={s.soil_key}>{s.name}</option>
              ))}
            </select>
            {activeSoil && (
              <p className="text-[10px] text-slate-400 mt-1">
                FC: <strong className="text-slate-300">{activeSoil.field_capacity_fc}</strong> | WP: <strong className="text-slate-300">{activeSoil.wilting_point_wp}</strong> | Infiltration α: <strong className="text-slate-300">{activeSoil.infiltration_alpha}</strong>
              </p>
            )}
          </div>

          <div>
            <div className="flex justify-between text-slate-400 mb-1">
              <label>Soil Moisture (θ)</label>
              <span className="text-white font-mono">{formData.volumetric_moisture} m³/m³</span>
            </div>
            <input type="range" min="0.04" max="0.50" step="0.01" name="volumetric_moisture" value={formData.volumetric_moisture} onChange={handleChange} className="w-full accent-emerald-400 bg-slate-950 h-1.5 rounded cursor-pointer" />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Elevation (meters ASL)</label>
            <input type="number" step="10" name="elevation_m" value={formData.elevation_m} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white font-mono focus:border-emerald-500 focus:outline-none" />
          </div>
        </div>

        {/* Pillar 3 & 4: Crop & Location */}
        <div className="space-y-3.5 bg-slate-800/40 p-4 rounded-xl border border-slate-800 shadow-inner">
          <div className="flex items-center space-x-1.5 border-b border-slate-700/50 pb-2">
            <MapPin className="w-4 h-4 text-amber-400" />
            <span className="font-bold text-amber-400 uppercase tracking-wider text-[11px]">3. Crop & Location</span>
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Crop Species</label>
            <select name="crop_type" value={formData.crop_type} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white capitalize focus:border-amber-500 focus:outline-none">
              {crops.map((c) => (
                <option key={c.crop_key} value={c.crop_key}>{c.name}</option>
              ))}
            </select>
            {activeCrop && (
              <p className="text-[10px] text-slate-400 mt-1">
                Kc: <strong className="text-slate-300">{activeCrop.kc_mid} (Peak)</strong> | Baseline Yield: <strong className="text-slate-300">{activeCrop.yield_baseline_ton_ha} t/ha</strong>
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-slate-400 mb-1">Stage</label>
              <select name="growth_stage" value={formData.growth_stage} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 text-white capitalize focus:border-amber-500 focus:outline-none">
                <option value="initial">Initial</option>
                <option value="mid">Mid</option>
                <option value="end">End</option>
                <option value="average">Avg</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Yield (t/ha)</label>
              <input type="number" step="1" name="custom_yield_ton_ha" value={formData.custom_yield_ton_ha} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 text-white font-mono focus:border-amber-500 focus:outline-none" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-slate-400 mb-1">Latitude (°)</label>
              <input type="number" step="0.1" name="latitude_deg" value={formData.latitude_deg} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 text-white font-mono" />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Longitude (°)</label>
              <input type="number" step="0.1" name="longitude_deg" value={formData.longitude_deg} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 text-white font-mono" />
            </div>
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full py-3.5 bg-gradient-to-r from-teal-500 via-emerald-500 to-teal-400 hover:from-teal-400 hover:to-emerald-400 text-slate-950 font-bold rounded-xl transition-all flex items-center justify-center space-x-2 shadow-lg shadow-teal-500/20 active:scale-[0.99]"
      >
        <Play className={`w-4 h-4 fill-slate-950 ${loading ? 'animate-spin' : ''}`} />
        <span>{loading ? 'Evaluating Model Inference via FastAPI...' : 'Execute Universal Crop Water Footprint Prediction'}</span>
      </button>
    </form>
  );
}
