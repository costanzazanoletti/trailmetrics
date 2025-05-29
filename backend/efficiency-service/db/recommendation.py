from db.core import fetch_all_sql_df
from db.setup import engine
def fetch_user_zone_segments(user_id, connection):
    """Fetches user's segments with efficiency zone info"""

    query = """
        select  
        s.segment_id ,
        s.start_distance, s.end_distance,
        s.segment_length,
        s.avg_gradient, 
        s.avg_cadence,
        s.grade_category,
        s.start_lat, s.end_lat ,
        s.start_lng, s.end_lng,
        s.start_altitude, s.end_altitude,
        s.start_time, s.end_time,
        s.start_heartrate, s.end_heartrate,
        s.avg_heartrate,
        s.avg_speed, 
        s.elevation_gain, 
        s.road_type, s.surface_type, 
        s.temperature,
        s.humidity,
        s.wind,
        s.weather_id, 
        s.cumulative_ascent, s.cumulative_descent,
        s.efficiency_score,
        sez.zone_among_similars, sez.zone_among_grade_category 
        FROM segments s 
        JOIN segment_efficiency_zone sez 
        ON s.segment_id = sez.segment_id 
        WHERE user_id = :user_id;
        """

    return fetch_all_sql_df(connection, query, {"user_id": user_id})