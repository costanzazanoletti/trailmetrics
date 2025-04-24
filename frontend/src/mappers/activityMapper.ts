import { Activity } from "../types/activity";

export interface CamelCaseActivity {
  id: number;
  name: string;
  distance: number;
  movingTime: number;
  totalElevationGain: number;
  athleteId: number;
  type: string;
  sportType: string;
  startDate: string;
  mapPolyline: string;
  averageSpeed: number;
  maxSpeed: number;
  averageCadence: number | null;
  averageTemp: number | null;
  averageWatts: number | null;
  weightedAverageWatts: number | null;
  hasHeartrate: boolean;
}

export function mapActivityFromApi(activity: Activity): CamelCaseActivity {
  return {
    id: activity.id,
    name: activity.name,
    distance: activity.distance,
    movingTime: activity.moving_time,
    totalElevationGain: activity.total_elevation_gain,
    athleteId: activity.athlete_id,
    type: activity.type,
    sportType: activity.sport_type,
    startDate: activity.start_date,
    mapPolyline: activity.map_polyline,
    averageSpeed: activity.average_speed,
    maxSpeed: activity.max_speed,
    averageCadence: activity.average_cadence,
    averageTemp: activity.average_temp,
    averageWatts: activity.average_watts,
    weightedAverageWatts: activity.weighted_average_watts,
    hasHeartrate: activity.has_heartrate,
  };
}
