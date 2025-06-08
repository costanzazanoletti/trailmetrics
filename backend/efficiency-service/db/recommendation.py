from db.core import fetch_all_sql_df, fetch_one_sql, execute_sql_batch, execute_sql
from exceptions.exceptions import DatabaseException
from sqlalchemy.exc import SQLAlchemyError

def fetch_user_zone_segments(user_id, engine):
    """
    Fetches user's segments of historic activities
    with efficiency zone info
    """
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
            JOIN segment_efficiency_zone sez ON s.segment_id = sez.segment_id
            JOIN activities a ON s.activity_id = a.id 
            WHERE a.athlete_id = :user_id AND a.id > 0;
            """
    
    try:
        with engine.begin() as connection:
            return fetch_all_sql_df(connection, query, {"user_id": user_id})
    except SQLAlchemyError as e:
        raise DatabaseException(f"An error occurred: {e}")
    
def fetch_activity_status(activity_id, engine):
    query = """
            SELECT 
                segment_status, 
                terrain_status, 
                weather_status, 
                not_processable, 
                prediction_executed_at
            FROM activity_status_tracker
            WHERE activity_id = :activity_id
        """
    try:
        with engine.connect() as connection:
            result = fetch_one_sql(connection, query, {"activity_id": activity_id})
            return dict(result._mapping) if result else None
    except SQLAlchemyError as e:
        raise DatabaseException(f"An error occurred: {e}")
    
def fetch_planned_segments_for_prediction(activity_id, engine):
    """
    Fetches planned segments for a given activity_id, returning columns required for prediction.
    """
    query = """
        SELECT 
            segment_id,
            user_id,
            segment_length,
            start_distance,
            end_distance,
            avg_gradient,
            start_altitude,
            elevation_gain,
            road_type,
            surface_type,
            temperature,
            humidity,
            wind,
            weather_id,
            cumulative_ascent,
            cumulative_descent
        FROM segments
        WHERE activity_id = :activity_id
    """
    try:
        with engine.begin() as connection:
            return fetch_all_sql_df(connection, query, {"activity_id": activity_id})
    except Exception as e:
        raise DatabaseException(f"Failed to fetch planned segments: {e}")

def update_prediction_and_activity_info(engine, activity_id, segments_data):
    """
    Updates predicted values in segments and overall activity info (moving_time, distance, total_elevation_gain)
    using the last segment's values. Executes all updates in a single transaction.
    """

    update_segments_query = """
        UPDATE segments
        SET 
            avg_speed = :avg_speed,
            avg_cadence = :avg_cadence,
            start_time = :start_time,
            end_time = :end_time,
            last_updated = CURRENT_TIMESTAMP
        WHERE segment_id = :segment_id
    """

    update_activity_query = """
        UPDATE activities
        SET 
            moving_time = :moving_time,
            distance = :distance,
            total_elevation_gain = :gain
        WHERE id = :activity_id
    """

    update_status_query = """
        UPDATE activity_status_tracker
        SET prediction_executed_at = CURRENT_TIMESTAMP
        WHERE activity_id = :activity_id
    """

    # Find the last valid segment
    valid_segments = [s for s in segments_data if s.get("end_time") is not None]
    if not valid_segments:
        raise DatabaseException("No valid segments found for prediction update.")

    last_segment = max(valid_segments, key=lambda s: s["end_distance"])
    moving_time = last_segment.get("end_time", 0)
    distance = last_segment["end_distance"]
    gain = last_segment.get("cumulative_ascent", 0)

    try:
        with engine.begin() as connection:
            execute_sql_batch(connection, update_segments_query, segments_data)
            execute_sql(connection, update_activity_query, {
                "activity_id": activity_id,
                "moving_time": moving_time,
                "distance": distance,
                "gain": gain
            })
            execute_sql(connection, update_status_query, {"activity_id": activity_id})
    except Exception as e:
        raise DatabaseException(f"Prediction update failed for activity {activity_id}: {e}")

def fetch_candidate_planned_activities(user_id, engine):
    """
    Returns planned activities (id < 0) with all statuses true and no prediction yet.
    """
    query = """
        SELECT a.id AS activity_id
        FROM activities a
        JOIN activity_status_tracker ast ON ast.activity_id = a.id
        WHERE a.athlete_id = :user_id
          AND a.id < 0
          AND ast.segment_status = TRUE
          AND ast.terrain_status = TRUE
          AND ast.weather_status = TRUE
          AND ast.prediction_executed_at IS NULL
          AND (ast.not_processable IS FALSE OR ast.not_processable IS NULL)
    """
    try:
        with engine.begin() as connection:
            df = fetch_all_sql_df(connection, query, {"user_id": user_id})
            return df["activity_id"].tolist()
    except SQLAlchemyError as e:
        raise DatabaseException(f"An error occurred: {e}")