export enum ActivityStatus {
  CREATED = 'CREATED',
  DATA_READY = 'DATA_READY',
  SIMILARITY_READY = 'SIMILARITY_READY',
  PREDICTION_READY = 'PREDICTION_READY',
  NOT_PROCESSABLE = 'NOT_PROCESSABLE',
}

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
  status: ActivityStatus | null;
}

export interface ActivityStream {
  latlng: [number, number][];
  altitude: number[];
  heartrate: number[];
  distance: number[];
  time: number[];
  speed: number[];
  grade: number[];
  cadence: number[];
}

export interface Segment {
  segmentId: string;
  activityId: number;
  startDistance: number;
  endDistance: number;
  avgGradient: number;
  avgCadence: number;
  startLat: number;
  endLat: number;
  startLng: number;
  endLng: number;
  startAltitude: number;
  endAltitude: number;
  startTime: number;
  endTime: number;
  avgSpeed: number;
  elevationGain: number;
  efficiencyScore: number;
  startHeartrate: number;
  endHeartrate: number;
  avgHeartrate: number;
  roadType: string;
  surfaceType: string;
  temperature: number;
  humidity: number;
  wind: number;
  weatherId: number;
  weatherMain: string;
  weatherDescription: string;
  weatherIcon: string;
  efficiencyZone: string;
  gradeEfficiencyZone: string;
  gradeCategory: number;
}

export interface PlannedActivityInput {
  name: string;
  distance: number;
  planned_duration: number; // seconds
  total_elevation_gain: number;
  type: string; // e.g., 'planned'
  sport_type: string; // 'Run' | 'Trail Run'
  start_date: string; // ISO string
}
