import React from 'react';
import { History, Database, RefreshCw } from 'lucide-react';

export default function AuditTable({ records, onRefresh, loading }) {
  return (
    <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-6 text-slate-200 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3.5">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 bg-teal-500/10 text-teal-400 rounded-lg border border-teal-500/20">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Real-Time Database Audit Trail</h2>
            <p className="text-[11px] text-slate-400">Live transaction records committed to SQLite/PostgreSQL (LocationPredictionRecord)</p>
          </div>
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors flex items-center space-x-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Records</span>
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-800/90 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
            <tr>
              <th className="px-3.5 py-3">Audit ID</th>
              <th className="px-3.5 py-3">Location Node</th>
              <th className="px-3.5 py-3">Crop Type</th>
              <th className="px-3.5 py-3">Soil Texture</th>
              <th className="px-3.5 py-3">Actual ET</th>
              <th className="px-3.5 py-3 text-emerald-400">Green CWF</th>
              <th className="px-3.5 py-3 text-sky-400">Blue CWF</th>
              <th className="px-3.5 py-3 text-teal-300">Total CWF</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80 font-mono">
            {!records || records.length === 0 ? (
              <tr>
                <td colSpan="8" className="px-4 py-8 text-center text-slate-500 font-sans">
                  <Database className="w-6 h-6 mx-auto mb-2 opacity-30 text-teal-400" />
                  No calculation audit records found in database.
                </td>
              </tr>
            ) : (
              records.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/50 transition-colors">
                  <td className="px-3.5 py-2.5 text-slate-400 font-mono">#{r.id}</td>
                  <td className="px-3.5 py-2.5 font-medium text-white font-sans">{r.location_label}</td>
                  <td className="px-3.5 py-2.5 capitalize font-sans">{r.crop_key}</td>
                  <td className="px-3.5 py-2.5 capitalize font-sans text-slate-400">{r.soil_key?.replace('_', ' ')}</td>
                  <td className="px-3.5 py-2.5 text-slate-200">{r.actual_et_mm?.toFixed(2)} mm</td>
                  <td className="px-3.5 py-2.5 text-emerald-400">{r.green_cwf_m3_ton?.toFixed(2)} m³/t</td>
                  <td className="px-3.5 py-2.5 text-sky-400">{r.blue_cwf_m3_ton?.toFixed(2)} m³/t</td>
                  <td className="px-3.5 py-2.5 font-bold text-teal-300 bg-teal-500/5">
                    {r.total_cwf_m3_ton?.toFixed(2)} m³/t
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
