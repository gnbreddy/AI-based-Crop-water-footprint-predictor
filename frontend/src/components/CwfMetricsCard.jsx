import React from 'react';
import { Droplets, Wind, Layers, Sun, ShieldAlert, Sparkles, CheckCircle, AlertTriangle } from 'lucide-react';

export default function CwfMetricsCard({ result }) {
  if (!result) {
    return (
      <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-8 text-center text-slate-500 h-full flex flex-col justify-center items-center shadow-lg">
        <div className="p-4 bg-teal-500/10 text-teal-400/50 rounded-2xl border border-teal-500/20 mb-3 animate-pulse">
          <Droplets className="w-10 h-10" />
        </div>
        <h3 className="text-base font-bold text-slate-300">Ready for Simulation</h3>
        <p className="text-xs text-slate-400 max-w-xs mt-1">
          Adjust physical parameters on the left and execute to generate verified Green/Blue CWF diagnostics.
        </p>
      </div>
    );
  }

  const cwf = result.crop_water_footprint_m3_ton;
  const diag = result.thermodynamic_diagnostics;
  const et = result.evapotranspiration_depths_mm;
  const stress = result.irrigation_stress_assessment;

  // Sustainability badge color
  const isCritical = stress?.includes('Critical');
  const isModerate = stress?.includes('Moderate');

  return (
    <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-6 text-slate-200 shadow-xl space-y-5">
      {/* Card Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3.5">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-base font-bold text-white tracking-tight">{result.location_label}</h2>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-slate-800 text-teal-300 border border-slate-700">
              {result.crop_name} ({result.soil_type})
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">Physical Energy & Moisture Partitioning</p>
        </div>

        {/* Stress Badge */}
        <div className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
          isCritical
            ? 'bg-rose-950/60 border-rose-500/50 text-rose-300'
            : isModerate
            ? 'bg-amber-950/60 border-amber-500/50 text-amber-300'
            : 'bg-emerald-950/60 border-emerald-500/50 text-emerald-300'
        }`}>
          {isCritical ? <ShieldAlert className="w-3.5 h-3.5" /> : isModerate ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
          <span>{stress}</span>
        </div>
      </div>

      {/* Main CWF 3-Metric Cards */}
      <div className="grid grid-cols-3 gap-3.5 text-center">
        {/* Green CWF */}
        <div className="bg-gradient-to-b from-slate-800/90 to-slate-900/90 p-4 rounded-xl border border-emerald-500/30 shadow-md">
          <div className="flex items-center justify-center space-x-1">
            <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">Green CWF</span>
          </div>
          <p className="text-2xl font-black text-white mt-1.5 tracking-tight">{cwf?.green_water_footprint_m3_ton?.toFixed(2)}</p>
          <div className="mt-1 flex items-center justify-center space-x-1">
            <span className="text-[11px] font-semibold text-emerald-400/90 font-mono">{cwf?.green_share_pct?.toFixed(1)}%</span>
            <span className="text-[10px] text-slate-400">m³/t (Rain)</span>
          </div>
        </div>

        {/* Blue CWF */}
        <div className="bg-gradient-to-b from-slate-800/90 to-slate-900/90 p-4 rounded-xl border border-sky-500/30 shadow-md">
          <div className="flex items-center justify-center space-x-1">
            <span className="text-[10px] uppercase font-bold text-sky-400 tracking-wider">Blue CWF</span>
          </div>
          <p className="text-2xl font-black text-white mt-1.5 tracking-tight">{cwf?.blue_water_footprint_m3_ton?.toFixed(2)}</p>
          <div className="mt-1 flex items-center justify-center space-x-1">
            <span className="text-[11px] font-semibold text-sky-400/90 font-mono">{cwf?.blue_share_pct?.toFixed(1)}%</span>
            <span className="text-[10px] text-slate-400">m³/t (Pumped)</span>
          </div>
        </div>

        {/* Total CWF */}
        <div className="bg-gradient-to-b from-teal-950/40 via-slate-800/90 to-slate-900/90 p-4 rounded-xl border border-teal-500/40 shadow-lg shadow-teal-500/10">
          <div className="flex items-center justify-center space-x-1">
            <Sparkles className="w-3 h-3 text-teal-300" />
            <span className="text-[10px] uppercase font-bold text-teal-300 tracking-wider">Total CWF</span>
          </div>
          <p className="text-2xl font-black text-teal-200 mt-1.5 tracking-tight">{cwf?.total_water_footprint_m3_ton?.toFixed(2)}</p>
          <span className="text-[10px] text-slate-400 block mt-1">m³ water / ton</span>
        </div>
      </div>

      {/* Evapotranspiration Depths */}
      <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800 grid grid-cols-3 gap-2 text-center text-xs">
        <div>
          <span className="text-[10px] text-slate-400 block">Actual ET</span>
          <strong className="text-white font-mono">{et?.actual_et_mm?.toFixed(2)} mm</strong>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block">Crop ET (Kc × ET)</span>
          <strong className="text-teal-300 font-mono">{et?.crop_adjusted_et_mm?.toFixed(2)} mm</strong>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block">Effective Rain</span>
          <strong className="text-emerald-400 font-mono">{et?.effective_precipitation_mm?.toFixed(2)} mm</strong>
        </div>
      </div>

      {/* Dimensionless Physical Diagnostics */}
      <div className="grid grid-cols-3 gap-2.5 text-xs">
        <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800 flex items-center space-x-2.5">
          <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg">
            <Wind className="w-4 h-4" />
          </div>
          <div>
            <p className="text-[10px] text-slate-400">Vapor Deficit (VPD)</p>
            <p className="font-bold text-slate-100 font-mono">{diag?.vapor_pressure_deficit_kpa?.toFixed(3)} kPa</p>
          </div>
        </div>

        <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800 flex items-center space-x-2.5">
          <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <p className="text-[10px] text-slate-400">Soil Stress (SSI)</p>
            <p className="font-bold text-slate-100 font-mono">{diag?.soil_stress_index_0_1?.toFixed(3)}</p>
          </div>
        </div>

        <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800 flex items-center space-x-2.5">
          <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg">
            <Sun className="w-4 h-4" />
          </div>
          <div>
            <p className="text-[10px] text-slate-400">FAO-56 Ref ET₀</p>
            <p className="font-bold text-slate-100 font-mono">{diag?.fao56_reference_et0_mm?.toFixed(2)} mm</p>
          </div>
        </div>
      </div>
    </div>
  );
}
