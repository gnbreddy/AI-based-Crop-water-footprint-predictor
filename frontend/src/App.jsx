import React, { lazy, Suspense, useState, useEffect } from 'react';
import Header from './components/Header';
import SimulationForm from './components/SimulationForm';
import CwfMetricsCard from './components/CwfMetricsCard';
import { predictCwf, fetchAuditRecords } from './api/cwfApi';

// Leaflet and charting libraries are relatively large; defer them until their
// panels are rendered so the simulation controls become interactive sooner.
const FootprintChart = lazy(() => import('./components/FootprintChart'));
const GeospatialMap = lazy(() => import('./components/GeospatialMap'));
const AuditTable = lazy(() => import('./components/AuditTable'));

export default function App() {
  const [predictionResult, setPredictionResult] = useState(null);
  const [auditRecords, setAuditRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recordsLoading, setRecordsLoading] = useState(false);
  
  // Coordinates for the map
  const [mapCoords, setMapCoords] = useState({
    lat: 16.7,
    lng: 74.2,
    label: 'Kolhapur Farm Block-A'
  });

  const loadAuditRecords = async () => {
    setRecordsLoading(true);
    try {
      const records = await fetchAuditRecords(15);
      setAuditRecords(records);
    } catch (err) {
      console.error('Failed to load audit records', err);
    } finally {
      setRecordsLoading(false);
    }
  };

  useEffect(() => {
    loadAuditRecords();
  }, []);

  const handleCoordsChange = (lat, lng, label) => {
    setMapCoords({ lat, lng, label });
  };

  const handlePredict = async (payload) => {
    setLoading(true);
    try {
      const res = await predictCwf(payload);
      setPredictionResult(res);
      setMapCoords({
        lat: payload.atmosphere.latitude_deg || 16.7,
        lng: payload.atmosphere.longitude_deg || 74.2,
        label: payload.location_label || 'Predicted Farm'
      });
      // Refresh audit records after commit
      await loadAuditRecords();
    } catch (err) {
      console.error('Prediction request failed', err);
      alert('Prediction failed. Make sure the FastAPI backend is running at http://127.0.0.1:8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-teal-500 selection:text-slate-950">
      <Header />

      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Form Controls (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <SimulationForm
              onPredict={handlePredict}
              loading={loading}
              onCoordsChange={handleCoordsChange}
            />
          </div>

          {/* Right Column: Output Metrics, Chart & Map (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <CwfMetricsCard result={predictionResult} />
            {predictionResult && (
              <Suspense fallback={<div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 text-sm text-slate-400">Loading footprint chart…</div>}>
                <FootprintChart result={predictionResult} />
              </Suspense>
            )}
            <Suspense fallback={<div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 text-sm text-slate-400">Loading map…</div>}>
              <GeospatialMap
                latitude={mapCoords.lat}
                longitude={mapCoords.lng}
                label={mapCoords.label}
                result={predictionResult}
              />
            </Suspense>
          </div>
        </div>

        {/* Bottom Full-Width Table: Real-Time Audit Records */}
        <Suspense fallback={<div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 text-sm text-slate-400">Loading audit trail…</div>}>
          <AuditTable
            records={auditRecords}
            onRefresh={loadAuditRecords}
            loading={recordsLoading}
          />
        </Suspense>
      </main>

      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500 bg-slate-900/50">
        AquaCrop AI Universal Agro-Hydrological Platform &bull; Powered by FastAPI, LightGBM, and FAO-56 Penman-Monteith
      </footer>
    </div>
  );
}
