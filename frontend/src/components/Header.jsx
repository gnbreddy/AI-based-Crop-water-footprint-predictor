import React, { useEffect, useState } from 'react';
import { Activity, Database, Cpu, CheckCircle2, XCircle, RefreshCw } from 'lucide-react';
import { checkHealth } from '../api/cwfApi';

export default function Header() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadHealth = async () => {
    try {
      const data = await checkHealth();
      setHealth(data);
    } catch (err) {
      setHealth({ status: 'offline', database: 'disconnected', ml_model_loaded: false });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const isOnline = health?.status === 'healthy';

  return (
    <header className="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 text-white px-6 py-4 flex flex-wrap justify-between items-center shadow-lg sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <div className="p-2.5 bg-teal-500/20 text-teal-400 rounded-xl border border-teal-500/30 shadow-inner">
          <Activity className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-teal-400 via-emerald-300 to-sky-400 bg-clip-text text-transparent">
              AquaCrop AI
            </h1>
            <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20">
              Universal CWF Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Physics-Informed LightGBM & FAO-56 Agro-Hydrological Prediction
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-3 mt-3 sm:mt-0 text-xs">
        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700">
          <Database className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-300">
            DB: <strong className="text-white">{health?.database || 'checking...'}</strong>
            {health?.registered_crops && ` (${health.registered_crops} Crops)`}
          </span>
        </div>

        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700">
          <Cpu className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-300">
            ML Model: <strong className={health?.ml_model_loaded ? 'text-teal-300' : 'text-slate-400'}>{health?.ml_model_loaded ? 'Active' : 'Offline'}</strong>
          </span>
        </div>

        <div className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border ${isOnline ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-400' : 'bg-rose-950/60 border-rose-500/40 text-rose-400'}`}>
          {isOnline ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
          <span className="font-bold uppercase tracking-wider">{isOnline ? 'Online' : 'Offline'}</span>
        </div>

        <button onClick={loadHealth} title="Refresh System Status" className="p-1.5 text-slate-400 hover:text-white rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </header>
  );
}
