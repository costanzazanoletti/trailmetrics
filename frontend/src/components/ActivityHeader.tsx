import { formatTime } from '../utils/formatUtils';
import { CamelCaseActivity } from '../mappers/activityMapper';

interface ActivityHeaderProps {
  activity: CamelCaseActivity;
}

export function ActivityHeader({ activity }: ActivityHeaderProps) {
  return (
    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
      <div>
        <div className="text-xs text-gray-500 mt-1"># {activity.id}</div>
        <h1 className="text-2xl font-semibold text-gray-600">
          {activity.name}
        </h1>
        <p className="text-gray-600 mt-2">
          {activity.sportType} | {new Date(activity.startDate).toLocaleString()}
        </p>
      </div>
      <div className="flex gap-6 mt-4 md:mt-0 text-sm text-gray-700">
        <div>
          <strong>Distance:</strong> {(activity.distance / 1000).toFixed(2)} km
        </div>
        <div>
          <strong>Duration:</strong> {formatTime(activity.movingTime)}
        </div>
        <div>
          <strong>Elevation:</strong> {activity.totalElevationGain} m
        </div>
      </div>
    </div>
  );
}
