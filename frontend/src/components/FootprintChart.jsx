import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { PieChart as ChartIcon } from 'lucide-react';

export default function FootprintChart({ result }) {
  if (!result || !result.crop_water_footprint_m3_ton) return null;

  const cwf = result.crop_water_footprint_m3_ton;
  const data = [
    { name: 'Green Water (Rainfall)', value: cwf.green_water_footprint_m3_ton || 0, color: '#10b981' },
    { name: 'Blue Water (Irrigation)', value: cwf.blue_water_footprint_m3_ton || 0, color: '#0ea5e9' },
  ];

  return (
    <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 text-slate-200 shadow-xl space-y-2">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center space-x-2">
          <ChartIcon className="w-4 h-4 text-teal-400" />
          <h3 className="text-sm font-bold text-white tracking-tight">Hydrological Partitioning Ratio</h3>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">Total: {cwf.total_water_footprint_m3_ton?.toFixed(2)} m³/t</span>
      </div>

      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              innerRadius={45}
              outerRadius={68}
              paddingAngle={4}
              dataKey="value"
              animationDuration={800}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => [`${Number(value).toFixed(2)} m³/ton`, 'Footprint']}
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px', color: '#f8fafc' }}
            />
            <Legend verticalAlign="bottom" height={32} wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
