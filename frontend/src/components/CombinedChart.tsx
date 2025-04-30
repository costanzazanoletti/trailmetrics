import { useState } from 'react';
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
  ReferenceArea,
} from 'recharts';
import { CustomTooltip } from './CustomTooltip';
import { Segment } from '../types/activity';

interface CombinedChartProps {
  time: number[];
  altitude: number[];
  heartrate: number[];
  cadence: number[];
  speed: number[];
  distance: number[];
  grade: number[];
  onHoverIndexChange?: (index: number) => void;
  highlightIndex?: number | null;
  segments?: Segment[];
  selectedSegmentId?: string;
  onSegmentClick?: (segment: Segment) => void;
}

export function CombinedChart({
  time,
  altitude,
  heartrate,
  cadence,
  speed,
  distance,
  grade,
  onHoverIndexChange,
  highlightIndex,
  segments = [],
  selectedSegmentId,
  onSegmentClick,
}: CombinedChartProps) {
  const [showHeartRate, setShowHeartRate] = useState(true);
  const [showCadence, setShowCadence] = useState(false);
  const [showPace, setShowPace] = useState(false);

  if (altitude.length === 0) return <p>No data</p>;

  const data = altitude.map((alt, index) => {
    const currentSpeed = speed[index];
    let pace = undefined;

    if (currentSpeed && currentSpeed > 0) {
      const speedKmH = currentSpeed * 3.6;
      const paceSecPerKm = 3600 / speedKmH;
      pace = paceSecPerKm / 60; // pace in min/km
    }

    return {
      x: distance[index] / 1000,
      altitude: alt,
      heartrate: heartrate[index],
      cadence: cadence[index],
      speed: currentSpeed,
      pace: pace,
      time: time[index],
      grade: grade[index],
    };
  });

  const minAltitude = Math.min(...altitude);
  const maxAltitude = Math.max(...altitude);

  return (
    <div className="w-full">
      <div className="flex gap-4 mb-4">
        <label className="text-sm">
          <input
            type="checkbox"
            checked={showHeartRate}
            onChange={() => setShowHeartRate((prev) => !prev)}
            className="mr-1"
          />
          Heart Rate
        </label>
        <label className="text-sm">
          <input
            type="checkbox"
            checked={showCadence}
            onChange={() => setShowCadence((prev) => !prev)}
            className="mr-1"
          />
          Cadence
        </label>
        <label className="text-sm">
          <input
            type="checkbox"
            checked={showPace}
            onChange={() => setShowPace((prev) => !prev)}
            className="mr-1"
          />
          Pace
        </label>
      </div>

      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={data}
            onMouseMove={(state) => {
              if (state && typeof state.activeTooltipIndex === 'number') {
                onHoverIndexChange?.(state.activeTooltipIndex);
              }
            }}
            onClick={(state) => {
              if (!state || typeof state.activeLabel !== 'number') return;
              const clickedKm = state.activeLabel;

              const found = segments?.find(
                (seg) =>
                  seg.startDistance / 1000 <= clickedKm &&
                  seg.endDistance / 1000 >= clickedKm
              );

              if (found && onSegmentClick) {
                onSegmentClick(found);
              }
            }}
          >
            <defs>
              <linearGradient id="altitudeGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#9CA3AF" stopOpacity={1} />
                <stop offset="95%" stopColor="#9CA3AF" stopOpacity={0.5} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" horizontal vertical={false} />

            <XAxis
              dataKey="x"
              type="number"
              domain={['dataMin', 'dataMax']}
              tickFormatter={(value) => `${value.toFixed(0)} km`}
            />
            <YAxis
              yAxisId="left"
              domain={[minAltitude - 20, maxAltitude + 20]}
              tickFormatter={(value) => `${value} m`}
              label={{
                value: 'Altitude (m)',
                angle: -90,
                position: 'insideLeft',
              }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tickFormatter={(value) => `${value}`}
              label={{
                value: 'HR / Cadence / Pace',
                angle: 90,
                position: 'insideRight',
              }}
            />

            <Tooltip content={<CustomTooltip />} />

            {segments.map((segment) => {
              const x1 = segment.startDistance / 1000;
              const x2 = segment.endDistance / 1000;
              const isSelected = segment.segmentId === selectedSegmentId;

              return (
                <ReferenceArea
                  key={segment.segmentId}
                  x1={x1}
                  x2={x2}
                  stroke={isSelected ? '#EF4444' : '#D1D5DB'}
                  fill={isSelected ? '#FECACA' : '#E5E7EB'}
                  fillOpacity={isSelected ? 0.3 : 0.15}
                  strokeOpacity={0.6}
                  ifOverflow="extendDomain"
                  yAxisId="left"
                />
              );
            })}

            <Area
              type="monotone"
              dataKey="altitude"
              yAxisId="left"
              stroke="none"
              fill="url(#altitudeGradient)"
              fillOpacity={0.5}
            />

            {showHeartRate && (
              <Line
                type="monotone"
                dataKey="heartrate"
                stroke="#EF4444"
                dot={false}
                strokeWidth={2}
                yAxisId="right"
              />
            )}
            {showCadence && (
              <Line
                type="monotone"
                dataKey="cadence"
                stroke="#3B82F6"
                dot={false}
                strokeWidth={2}
                yAxisId="right"
              />
            )}
            {showPace && (
              <Line
                type="monotone"
                dataKey="pace"
                stroke="#22C55E"
                dot={false}
                strokeWidth={2}
                yAxisId="right"
              />
            )}

            {typeof highlightIndex === 'number' && data[highlightIndex] && (
              <ReferenceDot
                x={data[highlightIndex].x}
                y={data[highlightIndex].altitude}
                yAxisId="left"
                r={4}
                fill="#1D4ED8"
                stroke="white"
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
