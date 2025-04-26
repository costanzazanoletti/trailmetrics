import { useState } from "react";
import { MapContainer, Polyline, TileLayer, useMap } from "react-leaflet";
import { LatLngBoundsExpression, LatLngExpression } from "leaflet";

interface MapWithTrackProps {
  latlng: [number, number][];
}

const tileLayers = {
  OpenStreetMap: {
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution: "&copy; OpenStreetMap contributors",
  },
  OpenTopoMap: {
    url: "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    attribution: "Map data: &copy; OpenTopoMap (CC-BY-SA)",
  },
  CartoDark: {
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution: "&copy; OpenStreetMap contributors & CartoDB",
  },
};

function FitBounds({ latlng }: { latlng: [number, number][] }) {
  const map = useMap();

  if (latlng.length > 0) {
    const bounds: LatLngBoundsExpression = latlng.map(([lat, lng]) => [lat, lng]);
    map.fitBounds(bounds, { padding: [20, 20] });
  }

  return null;
}

export function MapWithTrack({ latlng }: MapWithTrackProps) {
  const [selectedMap, setSelectedMap] = useState<keyof typeof tileLayers>("OpenStreetMap");

  if (latlng.length === 0) {
    return <p className="text-sm text-gray-500">No GPS data available.</p>;
  }

  const path: LatLngExpression[] = latlng.map(([lat, lng]) => [lat, lng]);
  const center = path[Math.floor(path.length / 2)];

  return (
    <div className="relative w-full">
      {/* Mappa */}
      <MapContainer
        center={center}
        zoom={13}
        style={{ height: "400px", width: "100%", borderRadius: "8px", overflow: "hidden", zIndex: 0 }}
      >
        <TileLayer
          url={tileLayers[selectedMap].url}
          attribution={tileLayers[selectedMap].attribution}
        />
        <Polyline positions={path} />
        <FitBounds latlng={latlng} />
      </MapContainer>

      {/* Dropdown sopra la mappa */}
      <div className="absolute top-2 left-2 z-[1000] bg-white rounded shadow p-2">
        <select
          value={selectedMap}
          onChange={(e) => setSelectedMap(e.target.value as keyof typeof tileLayers)}
          className="text-sm p-1 border rounded"
        >
          {Object.keys(tileLayers).map((key) => (
            <option key={key} value={key}>
              {key}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

