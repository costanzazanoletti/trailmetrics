import { useState } from "react";
import { ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, TooltipProps } from "recharts";
import { CustomTooltip } from "./CustomTooltip";

interface CombinedChartProps {
  time: number[];
  altitude: number[];
  heartrate: number[];
  cadence: number[];
  speed: number[];
  distance: number[];
  grade: number[]; 
}


export function CombinedChart({ time, altitude, heartrate, cadence, speed, distance, grade }: CombinedChartProps) {
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
            pace = paceSecPerKm / 60; // pace in min/km, float (es: 5.75 = 5'45")
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
      {/* Checkbox to select what to show */}
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

      {/* Chart */}
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data}>
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
                label={{ value: "Altitude (m)", angle: -90, position: "insideLeft" }}
            />

            <YAxis
                yAxisId="right"
                orientation="right"
                tickFormatter={(value) => `${value}`}
                label={{ value: "HR / Cadence / Pace", angle: 90, position: "insideRight" }}
            />

            <Tooltip content={<CustomTooltip />} />

            {/* Altitude Area */}
            <Area
              type="monotone"
              dataKey="altitude"
              yAxisId="left"
              stroke="none"
              fill="url(#altitudeGradient)"
              fillOpacity={0.5}
            />

            {/* Dynamic lines */}
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
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
