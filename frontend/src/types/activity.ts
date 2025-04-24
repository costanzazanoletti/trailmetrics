export interface Activity {
  id: number;
  name: string;
  distance: number; //meters
  moving_time: number; // seconds
  total_elevation_gain: number; // meters
  athlete_id: number;
  type: string;
  sport_type: string;
  start_date: string; // ISO string
  map_polyline: string;
  average_speed: number; // m/s
  max_speed: number; // m/s
  average_cadence: number | null;
  average_temp: number | null;
  average_watts: number | null;
  weighted_average_watts: number | null;
  has_heartrate: boolean;
}
