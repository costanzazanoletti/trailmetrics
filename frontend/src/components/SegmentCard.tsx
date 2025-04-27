import { Segment } from "../types/activity";
import { formatPace } from "../utils/formatUtils";

interface SegmentCardProps {
  segment: Segment;
  isSelected: boolean;
  onSelect: (segment: Segment) => void;
}

export function SegmentCard({ segment, isSelected, onSelect }: SegmentCardProps) {
  // Calcoli base
  const length = segment.endDistance && segment.startDistance
    ? ((segment.endDistance - segment.startDistance)).toFixed(0)
    : "N/A";

  const elevationGain = segment.elevationGain ?? "N/A";
  const avgGradient = segment.avgGradient?.toFixed(1) ?? "N/A";
  const avgSpeed = segment.avgSpeed? formatPace(segment.avgSpeed) : "N/A";
  const avgHeartrate = segment.avgHeartrate?.toFixed(0) ?? "N/A";
  const avgCadence = segment.avgCadence?.toFixed(0) ?? "N/A";

  const temperature = segment.temperature?.toFixed(1) ?? "N/A";
  const humidity = segment.humidity ?? "N/A";
  const wind = segment.wind?.toFixed(1) ?? "N/A";
  const weatherDescr = segment.weatherDescription ?? "N/A";

  const roadType = segment.roadType ?? "N/A";
  const surfaceType = segment.surfaceType ?? "N/A";

  // Weather Icon URL (API OpenWeather)
  const weatherIconUrl = segment.weatherIcon
    ? `https://openweathermap.org/img/wn/${segment.weatherIcon}@2x.png`
    : null;

  return (
    <div
      className={`p-3 rounded border ${
        isSelected ? "bg-blue-100 border-blue-400" : "bg-white"
      } hover:bg-blue-50 cursor-pointer transition`}
      onClick={() => onSelect(segment)}
    >
      <div className="flex justify-between items-center mb-2">
        <div className="text-sm font-semibold">
          {avgGradient}% | {length} m | {elevationGain > 0 ? '+' : ''}{elevationGain} m
        </div>
        {weatherIconUrl && (
          <img src={weatherIconUrl} alt={weatherDescr} className="w-8 h-8" />
        )}
      </div>

      <div className="text-xs text-gray-700">
        {avgCadence} spm | {avgSpeed} | {avgHeartrate} bpm
      </div>

      <div className="text-xs text-gray-600 mt-2">
        {roadType} | {surfaceType}
      </div>

      <div className="text-xs text-gray-600 mt-2">
        {temperature}°C | hum:{humidity}% | wind: {wind} km/h
      </div>
    </div>
  );
}
