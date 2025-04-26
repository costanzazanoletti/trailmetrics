import { TooltipProps } from "recharts";
import { formatTime, formatPace } from "../utils/formatUtils";

export function CustomTooltip({ active, payload }: TooltipProps<any, any>) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const point = payload[0].payload;

  const distanceKm = point.x?.toFixed(2) ?? "N/A";
  const timeFormatted = point.time !== undefined ? formatTime(point.time) : "N/A";

  let paceFormatted = "N/A";
  if (point.speed && point.speed > 0) {
    const speedKmH = point.speed * 3.6;
    const paceSecPerKm = 3600 / speedKmH;
    const paceMin = Math.floor(paceSecPerKm / 60);
    const paceSec = Math.round(paceSecPerKm % 60);
    paceFormatted = `${paceMin}:${paceSec.toString().padStart(2, '0')}/km`;
  }

  return (
    <div className="bg-white p-4 rounded-md shadow-md border border-gray-200 text-sm space-y-1">
      <p><span className="font-semibold text-gray-700">Time:</span> {timeFormatted}</p>
      <p><span className="font-semibold text-gray-700">Distance:</span> {distanceKm} km</p>

      {payload.map((entry, index) => {
        const { dataKey, stroke, value } = entry;
        let label = "";

        switch (dataKey) {
          case "heartrate":
            label = "Heart Rate";
            break;
          case "cadence":
            label = "Cadence";
            break;
          case "pace":
            label = "Pace";
            break;
          default:
            return null;
        }

        const formattedValue =
          dataKey === "pace"
            ? formatPace(point.speed)
            : dataKey === "cadence"
            ? `${point.cadence ?? 'N/A'} spm`
            : `${point.heartrate ?? 'N/A'} bpm`;

        return (
          <p key={index}>
            <span className="font-semibold" style={{ color: stroke }}>
              {label}:
            </span>{" "}
            {formattedValue}
          </p>
        );
      })}

      <p><span className="font-semibold text-green-600">Grade:</span> {point.grade !== undefined ? `${point.grade.toFixed(2)} %` : "N/A"}</p>
    </div>
  );
}
