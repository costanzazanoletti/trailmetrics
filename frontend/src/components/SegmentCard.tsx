import {
  Heart,
  Ruler,
  TrendingUp,
  GaugeCircle,
  Route,
  LandPlot,
} from 'lucide-react';
import { Segment } from '../types/activity';
import { formatPace } from '../utils/formatUtils';
import { EfficiencyIcon } from './EfficiencyIcon';

interface SegmentCardProps {
  segment: Segment;
  isSelected: boolean;
  onSelect: (segment: Segment) => void;
}

export function SegmentCard({
  segment,
  isSelected,
  onSelect,
}: SegmentCardProps) {
  const length =
    segment.endDistance && segment.startDistance
      ? (segment.endDistance - segment.startDistance).toFixed(0)
      : 'N/A';
  const elevationGain = segment.elevationGain ?? 'N/A';
  const avgGradient = segment.avgGradient?.toFixed(1) ?? 'N/A';
  const avgSpeed = segment.avgSpeed ? formatPace(segment.avgSpeed) : 'N/A';
  const avgHeartrate = segment.avgHeartrate?.toFixed(0) ?? 'N/A';
  const avgCadence = segment.avgCadence?.toFixed(0) ?? 'N/A';

  const temperature = segment.temperature?.toFixed(1) ?? 'N/A';
  const humidity = segment.humidity ?? 'N/A';
  const wind = segment.wind?.toFixed(1) ?? 'N/A';
  const weatherDescr = segment.weatherDescription ?? 'N/A';

  const roadType = segment.roadType ?? 'N/A';
  const surfaceType = segment.surfaceType ?? 'N/A';

  const weatherIconUrl = segment.weatherIcon
    ? `https://openweathermap.org/img/wn/${segment.weatherIcon}@2x.png`
    : null;

  return (
    <div
      className={`p-3 rounded border ${
        isSelected ? 'bg-blue-100 border-blue-400' : 'bg-white'
      } hover:bg-blue-50 cursor-pointer transition`}
      onClick={() => onSelect(segment)}
    >
      <div className="flex justify-between items-start mb-2">
        <div className="flex flex-col text-sm font-semibold">
          <span>{avgGradient}% grade</span>
          <span>{avgCadence} spm cadence</span>
        </div>
        <div className="flex gap-2">
          {segment.efficiencyZone && (
            <EfficiencyIcon zone={segment.efficiencyZone} type="efficiency" />
          )}
          {segment.gradeEfficiencyZone && (
            <EfficiencyIcon zone={segment.gradeEfficiencyZone} type="grade" />
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 text-xs text-gray-700">
        <Heart size={14} className="text-red-500" /> {avgHeartrate} bpm
        <GaugeCircle size={14} className="text-blue-500" /> {avgSpeed}
      </div>

      <div className="flex items-center gap-3 text-xs text-gray-700 mt-2">
        <Ruler size={14} /> {length} m
        <TrendingUp size={14} /> {elevationGain} m D+
      </div>

      <div className="flex items-center gap-3 text-xs text-gray-600 mt-2">
        <Route size={14} /> {roadType}
        <LandPlot size={14} /> {surfaceType}
      </div>

      <div className="flex items-center gap-3 text-xs text-gray-600 mt-2">
        {weatherIconUrl && (
          <img
            src={weatherIconUrl}
            alt={weatherDescr}
            title={weatherDescr}
            className="w-6 h-6"
          />
        )}
        {temperature}°C | hum: {humidity}% | wind: {wind} km/h
      </div>
    </div>
  );
}
