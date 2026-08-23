import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { MapPin } from 'lucide-react';
import L from 'leaflet';

// Fix standard Leaflet default marker icons for Webpack/Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Component to dynamically pan and re-center map when coordinates change
function MapRecenter({ lat, lng }) {
  const map = useMap();
  useEffect(() => {
    if (lat && lng) {
      map.flyTo([lat, lng], 8, { duration: 1.2 });
    }
  }, [lat, lng, map]);
  return null;
}

export default function GeospatialMap({ latitude = 16.7, longitude = 74.2, label = 'ROI Node', result }) {
  const position = [latitude, longitude];

  return (
    <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 text-slate-200 shadow-xl space-y-3">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center space-x-2">
          <MapPin className="w-4 h-4 text-teal-400" />
          <h3 className="text-sm font-bold text-white tracking-tight">Geospatial Regional Context</h3>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">
          Lat: {latitude.toFixed(2)}°, Lon: {longitude.toFixed(2)}°
        </span>
      </div>

      <div className="h-56 w-full rounded-xl overflow-hidden border border-slate-800 relative z-0">
        <MapContainer
          center={position}
          zoom={8}
          scrollWheelZoom={false}
          className="h-full w-full"
        >
          <MapRecenter lat={latitude} lng={longitude} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={position}>
            <Popup>
              <div className="text-slate-950 text-xs font-sans p-1">
                <p className="font-bold text-sm border-b pb-1 mb-1">{label}</p>
                {result ? (
                  <>
                    <p className="font-semibold text-teal-700">Total CWF: {result.crop_water_footprint_m3_ton?.total_water_footprint_m3_ton?.toFixed(2)} m³/t</p>
                    <p className="text-slate-600">Green: {result.crop_water_footprint_m3_ton?.green_share_pct?.toFixed(1)}% | Blue: {result.crop_water_footprint_m3_ton?.blue_share_pct?.toFixed(1)}%</p>
                    <p className="text-[10px] text-slate-500 mt-1">Crop: {result.crop_name} ({result.soil_type})</p>
                  </>
                ) : (
                  <p className="text-slate-500">Coordinates: {latitude.toFixed(2)}, {longitude.toFixed(2)}</p>
                )}
              </div>
            </Popup>
          </Marker>
        </MapContainer>
      </div>
    </div>
  );
}
