import {
  Heart,
  Ruler,
  TrendingUp,
  GaugeCircle,
  Route,
  LandPlot,
} from 'lucide-react';
import { getShortSegmentId } from '../utils/formatUtils';
import { Segment } from '../types/activity';
import { formatPace } from '../utils/formatUtils';
import { EfficiencyIcon } from './EfficiencyIcon';

interface SegmentCardProps {
  segment: Segment;
  isSelected: boolean;
  onSelect: (segment: Segment) => void;
  onShowSimilar?: () => void;
  variant?: 'full' | 'compact';
  currentActivityId?: number;
}

export function SegmentCard({
  segment,
  isSelected,
  onSelect,
  onShowSimilar,
  variant = 'full',
  currentActivityId,
}: SegmentCardProps) {
  const shortId = getShortSegmentId(segment.segmentId);
  const isSameActivity =
    !currentActivityId || segment.activityId === currentActivityId;

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

  // Handler for clicking the card or efficiency icon
  const handleClick = () => {
    if (variant === 'compact') {
      if (isSameActivity) {
        onSelect(segment);
      } else {
        window.open(
          `/activities/${segment.activityId}?segment=${segment.segmentId}`,
          '_blank'
        );
      }
    } else {
      onSelect(segment);
    }
  };

  return (
    <div
      className={`p-3 rounded border ${
        isSelected ? 'bg-blue-100 border-blue-400' : 'bg-white'
      } hover:bg-blue-50 cursor-pointer transition`}
      onClick={handleClick}
    >
      <div className="flex justify-between items-start mb-2">
        <div className="flex flex-col text-sm font-semibold">
          <span className="text-xs text-gray-500 mb-2">
            #{isSameActivity ? shortId : segment.segmentId}
          </span>
          <span>{avgGradient}% grade</span>
          <span>{avgCadence} spm cadence</span>
        </div>
        {variant === 'full' && onShowSimilar ? (
          <div
            className="relative group cursor-pointer"
            onClick={(e) => {
              e.stopPropagation();
              onShowSimilar();
            }}
          >
            <div className="flex gap-2 p-1 rounded hover:bg-blue-100 transition">
              {segment.efficiencyZone && (
                <EfficiencyIcon
                  zone={segment.efficiencyZone}
                  type="efficiency"
                />
              )}
              {segment.gradeEfficiencyZone && (
                <EfficiencyIcon
                  zone={segment.gradeEfficiencyZone}
                  type="grade"
                />
              )}
            </div>

            {/* Tooltip */}
            <div
              className="absolute top-full left-1/2 -translate-x-1/2 mt-1 
                  bg-gray-800 text-white text-xs px-2 py-1 rounded shadow 
                  opacity-0 group-hover:opacity-100 transition-opacity duration-150 z-10 pointer-events-none"
            >
              Show similar segments
            </div>
          </div>
        ) : (
          <div className="flex gap-2">
            {segment.efficiencyZone && (
              <EfficiencyIcon zone={segment.efficiencyZone} type="efficiency" />
            )}
            {segment.gradeEfficiencyZone && (
              <EfficiencyIcon zone={segment.gradeEfficiencyZone} type="grade" />
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-3 text-xs text-gray-700">
        <Heart size={14} className="text-red-500" /> {avgHeartrate} bpm
        <GaugeCircle size={14} className="text-blue-500" /> {avgSpeed}
      </div>

      {variant === 'full' && (
        <>
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
        </>
      )}
    </div>
  );
}
