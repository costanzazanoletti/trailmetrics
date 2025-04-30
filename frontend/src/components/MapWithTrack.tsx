import { useState, useEffect } from 'react';
import {
  MapContainer,
  Polyline,
  TileLayer,
  useMap,
  Marker,
} from 'react-leaflet';
import { LatLngBoundsExpression, LatLngExpression } from 'leaflet';
import L from 'leaflet';
import { Segment } from '../types/activity';

interface MapWithTrackProps {
  latlng: [number, number][];
  segments: Segment[];
  selectedSegmentId?: string;
  onSelectSegment?: (segment: Segment | null) => void;
  highlightIndex?: number | null;
}

const tileLayers = {
  OpenStreetMap: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap contributors',
  },
  OpenTopoMap: {
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: 'Map data: &copy; OpenTopoMap (CC-BY-SA)',
  },
  CartoDark: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap contributors & CartoDB',
  },
};

const highlightIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  iconSize: [20, 32],
  iconAnchor: [10, 32],
});

function FitBounds({
  latlng,
  selectedSegment,
}: {
  latlng: [number, number][];
  selectedSegment?: Segment;
}) {
  const map = useMap();

  useEffect(() => {
    if (selectedSegment) {
      const bounds: LatLngBoundsExpression = [
        [selectedSegment.startLat, selectedSegment.startLng],
        [selectedSegment.endLat, selectedSegment.endLng],
      ];
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (latlng.length > 0) {
      const bounds: LatLngBoundsExpression = latlng.map(([lat, lng]) => [
        lat,
        lng,
      ]);
      map.fitBounds(bounds, { padding: [20, 20] });
    }
  }, [latlng, selectedSegment, map]);

  return null;
}

export function MapWithTrack({
  latlng,
  segments,
  selectedSegmentId,
  onSelectSegment,
  highlightIndex,
}: MapWithTrackProps) {
  const [selectedMap, setSelectedMap] =
    useState<keyof typeof tileLayers>('OpenStreetMap');

  if (latlng.length === 0) {
    return <p className="text-sm text-gray-500">No GPS data available.</p>;
  }

  const path: LatLngExpression[] = latlng.map(([lat, lng]) => [lat, lng]);
  const center = path[Math.floor(path.length / 2)];
  const selectedSegment = segments.find(
    (seg) => seg.segmentId === selectedSegmentId
  );

  const highlightPosition =
    typeof highlightIndex === 'number' && latlng[highlightIndex]
      ? latlng[highlightIndex]
      : null;

  return (
    <div className="relative w-full">
      {/* Map */}
      <MapContainer
        center={center}
        zoom={13}
        style={{
          height: '400px',
          width: '100%',
          borderRadius: '8px',
          overflow: 'hidden',
          zIndex: 0,
        }}
      >
        <TileLayer
          url={tileLayers[selectedMap].url}
          attribution={tileLayers[selectedMap].attribution}
        />

        {highlightPosition && (
          <Marker position={highlightPosition} icon={highlightIcon} />
        )}

        {/* Main track */}
        <Polyline positions={latlng} color="blue" weight={3} />

        {/* Segments */}
        {segments.map((segment) => (
          <Polyline
            key={`${segment.segmentId}-${selectedSegmentId}`}
            positions={[
              [segment.startLat, segment.startLng],
              [segment.endLat, segment.endLng],
            ]}
            color={
              segment.segmentId.trim() === selectedSegmentId?.trim()
                ? 'red'
                : 'orange'
            }
            weight={
              segment.segmentId.trim() === selectedSegmentId?.trim() ? 8 : 4
            }
            dashArray={
              segment.segmentId.trim() === selectedSegmentId?.trim()
                ? undefined
                : '5'
            }
            eventHandlers={{
              click: () => {
                if (onSelectSegment) {
                  if (segment.segmentId === selectedSegmentId) {
                    onSelectSegment(null);
                  } else {
                    onSelectSegment(segment);
                  }
                }
              },
            }}
          />
        ))}

        {/* Fit bounds logic */}
        <FitBounds latlng={latlng} selectedSegment={selectedSegment} />
      </MapContainer>

      {/* Dropdown sopra la mappa */}
      <div className="absolute top-2 right-2 z-[1000] bg-white rounded shadow p-2">
        <select
          value={selectedMap}
          onChange={(e) =>
            setSelectedMap(e.target.value as keyof typeof tileLayers)
          }
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
