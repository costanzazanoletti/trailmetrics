import os
import sys
import logging
import logging_setup
import pandas as pd
from sqlalchemy import create_engine, text, bindparam
from dotenv import load_dotenv
from app.exceptions import DatabaseException
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("app")

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if "pytest" in sys.modules:
    DATABASE_URL = os.getenv("TEST_DATABASE_URL", DATABASE_URL)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set.")

print(f"Database URL: {DATABASE_URL}")

# Use parameter echo=True to log the queries
engine = create_engine(DATABASE_URL)

# Helper functions to handle connection and transactions
def execute_sql(connection, query, params=None):
    """Helper function to execute SQL using SQLAlchemy with a provided connection.
    Automatically handles expanding bind parameters for lists (for use with IN clauses).
    """
    try:
        stmt = text(query) 
        if params:
            for key, value in params.items():
                if isinstance(value, (list, tuple)):
                    stmt = stmt.bindparams(bindparam(key, expanding=True))
        result = connection.execute(stmt, params)
        return result
    except Exception as e:
        raise DatabaseException(f"Database error: {e}")

def fetch_one_sql(connection, query, params=None):
    """Helper function to fetch one result using SQLAlchemy with a provided connection."""
    try:
        stmt = text(query)
        if params:
            for key, value in params.items():
                if isinstance(value, (list, tuple)):
                    stmt = stmt.bindparams(bindparam(key, expanding=True)) 
        result = connection.execute(stmt, params).fetchone()
        return result
    except Exception as e:
        raise DatabaseException(f"Database error: {e}")

def fetch_all_sql_df(connection, query, params=None):
    """Fetch all results and return a pandas DataFrame."""
    try:
        stmt = text(query)
        if params:
            for key, value in params.items():
                if isinstance(value, (list, tuple)):
                    stmt = stmt.bindparams(bindparam(key, expanding=True))
        result = connection.execute(stmt, params)
        rows = result.fetchall()
        return pd.DataFrame(rows, columns=result.keys())
    except Exception as e:
        raise DatabaseException(f"Database error: {e}")

# Custom functions
def delete_all_data(engine):
    """Delete all segments and activity_status_tracker using SQLAlchemy."""
    try:
        with engine.begin() as connection:
            query_similarity = "DELETE FROM segment_similarity WHERE segment_id IS NOT NULL"
            query_segments = "DELETE FROM segments WHERE activity_id IS NOT NULL"
            query_status = "DELETE FROM activity_status_tracker WHERE activity_id IS NOT NULL"
            query_weather_progress = "DELETE FROM weather_data_progress WHERE activity_id IS NOT NULL"
            execute_sql(connection, query_similarity)
            execute_sql(connection, query_segments)
            execute_sql(connection, query_status)
            execute_sql(connection, query_weather_progress)
    except SQLAlchemyError as e:
        raise DatabaseException(f"Database error: {e}")
    
def delete_all_data_by_activity_ids(activity_ids, engine=engine):
    """Delete all segments and activity_status_tracker and similarity data."""
    try:
        with engine.begin() as connection:
            query_similarity = """
                                DELETE FROM segment_similarity
                                WHERE segment_id IN (SELECT segment_id FROM segments WHERE activity_id IN :activity_ids)
                                OR similar_segment_id IN (SELECT segment_id FROM segments WHERE activity_id IN :activity_ids)
                            """
            query_segments = "DELETE FROM segments WHERE activity_id in :activity_ids"
            query_status = "DELETE FROM activity_status_tracker WHERE activity_id in :activity_ids"
            query_weather_progress = "DELETE FROM weather_data_progress WHERE activity_id in :activity_ids"
            execute_sql(connection, query_similarity, {"activity_ids": activity_ids})
            execute_sql(connection, query_segments, {"activity_ids": activity_ids})
            execute_sql(connection, query_status, {"activity_ids": activity_ids})
            execute_sql(connection, query_weather_progress, {"activity_ids": activity_ids})
    except SQLAlchemyError as e:
        raise DatabaseException(f"Database error: {e}")

def segments_batch_insert_and_update_status(segments_df, activity_id, engine):
    """Batch insert segments and update activity status in transaction using SQLAlchemy."""
    try:
        with engine.begin() as connection:
            query = text("""
                INSERT INTO segments (segment_id, activity_id,  start_distance, end_distance, segment_length,
                    avg_gradient, avg_cadence, movement_type, "type", grade_category,
                    start_lat, start_lng, end_lat, end_lng, start_altitude, end_altitude,
                    start_time, end_time, start_heartrate, end_heartrate, avg_heartrate,
                    avg_speed, elevation_gain, hr_drift, efficiency_score, user_id)
                VALUES (:segment_id, :activity_id, :start_distance, :end_distance, :segment_length,
                        :avg_gradient, :avg_cadence, :movement_type, :type, :grade_category,
                        :start_lat, :start_lng, :end_lat, :end_lng, :start_altitude, :end_altitude,
                        :start_time, :end_time, :start_heartrate, :end_heartrate, :avg_heartrate,
                        :avg_speed, :elevation_gain, :hr_drift, :efficiency_score, :user_id)
                ON CONFLICT (segment_id)
                DO UPDATE
                SET
                    activity_id = EXCLUDED.activity_id,
                    start_distance = EXCLUDED.start_distance,
                    end_distance = EXCLUDED.end_distance,
                    segment_length = EXCLUDED.segment_length,
                    avg_gradient = EXCLUDED.avg_gradient,
                    avg_cadence = EXCLUDED.avg_cadence,
                    movement_type = EXCLUDED.movement_type,
                    "type" = EXCLUDED."type",
                    grade_category = EXCLUDED.grade_category,
                    start_lat = EXCLUDED.start_lat,
                    start_lng = EXCLUDED.start_lng,
                    end_lat = EXCLUDED.end_lat,
                    end_lng = EXCLUDED.end_lng,
                    start_altitude = EXCLUDED.start_altitude,
                    end_altitude = EXCLUDED.end_altitude,
                    start_time = EXCLUDED.start_time,
                    end_time = EXCLUDED.end_time,
                    start_heartrate = EXCLUDED.start_heartrate,
                    end_heartrate = EXCLUDED.end_heartrate,
                    avg_heartrate = EXCLUDED.avg_heartrate,
                    avg_speed = EXCLUDED.avg_speed,
                    elevation_gain = EXCLUDED.elevation_gain,
                    hr_drift = EXCLUDED.hr_drift,
                    efficiency_score = EXCLUDED.efficiency_score,
                    user_id = EXCLUDED.user_id,                    
                    last_updated = CURRENT_TIMESTAMP
            """)
            segments_data = segments_df.to_dict(orient='records')
            connection.execute(query, segments_data)
            logger.info(f"Executed segments batch store for activity {activity_id}")

            update_status_query = text("""
                INSERT INTO activity_status_tracker(activity_id, segment_status)
                VALUES (:activity_id, TRUE)
                ON CONFLICT (activity_id)
                DO UPDATE
                SET
                    segment_status = TRUE,
                    last_updated = CURRENT_TIMESTAMP;
            """)
            connection.execute(update_status_query, {"activity_id": activity_id})
            logger.info(f"Updated segment status for activity {activity_id}")
            
    except SQLAlchemyError as e:
        connection.rollback()
        raise DatabaseException(f"An error occurred: {e}")

def insert_not_processable_actitivity_status(activity_id, engine):
    try:
        with engine.begin() as connection:
            query = """
                    INSERT INTO activity_status_tracker(activity_id, not_processable)
                    VALUES (:activity_id, TRUE)
                    ON CONFLICT (activity_id)
                    DO UPDATE
                    SET
                        not_processable = TRUE,
                        last_updated = CURRENT_TIMESTAMP;
        
                """

            execute_sql(connection, query, {"activity_id": activity_id})
    except SQLAlchemyError as e:
        raise DatabaseException(f"An error occurred: {e}")

def terrain_batch_insert_and_update_status(segments_df, activity_id, engine):
    """Batch insert segment terrain info and update activity status in transaction using SQLAlchemy."""
    try:
        with engine.begin() as connection:  # Use context manager for transaction
            query = text("""
                INSERT INTO segments (segment_id, road_type, surface_type, activity_id)
                VALUES (:segment_id, :highway, :surface, :activity_id)
                ON CONFLICT (segment_id)
                DO UPDATE
                SET
                    road_type = EXCLUDED.road_type,
                    surface_type = EXCLUDED.surface_type,
                    activity_id = EXCLUDED.activity_id,
                    last_updated = CURRENT_TIMESTAMP
            """)

            segments_data = segments_df[['segment_id', 'highway', 'surface']].to_dict(orient='records')
            for row in segments_data:
                row['activity_id'] = activity_id
                
            connection.execute(query, segments_data)

            logger.info(f"Executed segment terrain info batch store for activity {activity_id}")

            update_status_query = text("""
                INSERT INTO activity_status_tracker(activity_id, terrain_status)
                VALUES (:activity_id, TRUE)
                ON CONFLICT (activity_id)
                DO UPDATE
                SET
                    terrain_status = TRUE,
                    last_updated = CURRENT_TIMESTAMP;
            """)
            connection.execute(update_status_query, {"activity_id": activity_id})
            logger.info(f"Updated terrain status for activity {activity_id}")

    except SQLAlchemyError as e:
        logger.error(f"Error saving terrain data to database: {e}")
        raise DatabaseException(f"An error occurred while saving terrain data: {e}")

def weather_batch_insert_and_update_status(weather_df, activity_id, group_id, total_groups, engine):
    """
    Batch insert weather data and update weather data progress using SQLAlchemy.
    If progress is complete, update activity status in transaction.
    """
    try:
        with engine.begin() as connection:
            # Insert or update weather data in segments table
            query = text("""
                INSERT INTO segments (segment_id, temperature, feels_like, humidity, wind,
                                      weather_id, weather_main, weather_description, activity_id)
                VALUES (:segment_id, :temp, :feels_like, :humidity, :wind,
                        :weather_id, :weather_main, :weather_description, :activity_id)
                ON CONFLICT (segment_id)
                DO UPDATE
                SET
                    temperature = EXCLUDED.temperature,
                    feels_like = EXCLUDED.feels_like,
                    humidity = EXCLUDED.humidity,
                    wind = EXCLUDED.wind,
                    weather_id = EXCLUDED.weather_id,
                    weather_main = EXCLUDED.weather_main,
                    weather_description = EXCLUDED.weather_description,
                    activity_id = EXCLUDED.activity_id,
                    last_updated = CURRENT_TIMESTAMP
            """)

            weather_data_records = weather_df.to_dict(orient='records')
            for record in weather_data_records:
                record['activity_id'] = activity_id
                
            connection.execute(query, weather_data_records)

            logger.info(f"Executed segment weather info batch store for activity {activity_id} group {group_id}")

            # Update weather data progress
            update_progress_query = text("""
                INSERT INTO weather_data_progress (activity_id, group_id, total_groups, saved)
                VALUES (:activity_id, :group_id, :total_groups, TRUE)
                ON CONFLICT (activity_id, group_id)
                DO UPDATE
                SET
                    saved = TRUE,
                    last_updated = CURRENT_TIMESTAMP;
            """)
            connection.execute(update_progress_query, {"activity_id": activity_id, "group_id": group_id, "total_groups": total_groups})
            logger.info(f"Executed weather data progress update for activity {activity_id} group {group_id}")

            # Check if all groups are saved
            check_progress_query = text("""
                SELECT COUNT(*)
                FROM weather_data_progress
                WHERE activity_id = :activity_id;
            """)
            result = connection.execute(check_progress_query, {"activity_id": activity_id}).scalar_one()
            all_groups_saved = result
            logger.info(f"Saved {all_groups_saved} of {total_groups} groups for activity {activity_id}")

            # Update activity status if all weather data is processed
            if all_groups_saved == total_groups:
                update_status_query = text("""
                    INSERT INTO activity_status_tracker(activity_id, weather_status)
                    VALUES (:activity_id, TRUE)
                    ON CONFLICT (activity_id)
                    DO UPDATE
                    SET
                        weather_status = TRUE,
                        last_updated = CURRENT_TIMESTAMP;
                """)
                connection.execute(update_status_query, {"activity_id": activity_id})
                logger.info(f"Updated weather status for activity {activity_id}")

    except SQLAlchemyError as e:
        logger.error(f"Error saving weather data to database: {e}")
        raise DatabaseException(f"An error occurred while saving weather data: {e}")

def get_user_segments(connection, user_id):
    """
    Retrieves all segments associated with a given user ID from the database and returns a Pandas DataFrame.
    """
    query = """
                SELECT 
                    segment_id, 
                    activity_id, 
                    grade_category,
                    segment_length,        
                    start_distance,       
                    start_time,           
                    start_altitude,       
                    elevation_gain,       
                    avg_gradient,    
                    road_type,       
                    surface_type,      
                    temperature,         
                    humidity,             
                    wind,              
                    weather_id
                FROM segments
                WHERE user_id = :user_id
            """
    return fetch_all_sql_df(connection, query, {"user_id": user_id})

def get_activity_status_fingerprint(connection, user_id):
    """Get activities and activitys status for a given user, with fingerprint."""
    query = """
                SELECT
                    COUNT(*) AS total_activities,
                    COUNT(*) FILTER (
                        WHERE 
                            (segment_status AND terrain_status AND weather_status)
                            OR not_processable
                    ) AS completed_activities,
                    md5(string_agg(activity_id::TEXT, ',' ORDER BY activity_id)) AS fingerprint
                FROM (
                    SELECT DISTINCT a.id AS activity_id, ast.segment_status, ast.terrain_status, ast.weather_status, ast.not_processable
                    FROM activities a
                    LEFT JOIN activity_status_tracker ast ON ast.activity_id = a.id
                    WHERE a.athlete_id = :user_id
                ) sub;
            """
    return fetch_one_sql(connection, query, {"user_id": user_id})

def get_similarity_status_fingerprint(connection, user_id):
    """Gets the similarity status fingerprint and the in progress state for the given user"""
    query = """
                SELECT activity_fingerprint, in_progress 
                FROM similarity_status_fingerprint 
                WHERE user_id = :user_id;
                """
    return fetch_one_sql(connection, query, {"user_id": user_id})

def update_similarity_status_fingerprint(connection, user_id, activity_fingerprint):
    query = """
        INSERT INTO similarity_status_fingerprint (user_id, in_progress, similarity_calculated_at, activity_fingerprint)
        VALUES (:user_id, true, now(), :fingerprint)
        ON CONFLICT (user_id) DO UPDATE
        SET in_progress = true,
            similarity_calculated_at = now(),
            activity_fingerprint = EXCLUDED.activity_fingerprint;
    """
    execute_sql(connection, query, {"user_id": user_id, "fingerprint": activity_fingerprint})

def update_similarity_status_in_progress(engine, user_id, in_progress):
    try:
        with engine.begin() as connection:
            query = """
                UPDATE similarity_status_fingerprint 
                SET in_progress = :in_progress
                WHERE user_id = :user_id
            """
            execute_sql(connection, query, {"user_id": user_id, "in_progress": in_progress})
            logger.info(f"Updated in_progress similarity status for user {user_id} to {in_progress}")
    except SQLAlchemyError as e:
        logger.error(f"Database error during similarity status update for user {user_id}: {e}")
        raise DatabaseException(f"Database error: {e}")
    
def delete_user_similarity_data(connection, user_id):
    """
    Deletes similarity scores from the segment_similarity table
    where either segment_id or similar_segment_id belongs to the given user's segments.
    """
    query = """
            DELETE FROM segment_similarity
            WHERE segment_id IN (SELECT segment_id FROM segments WHERE user_id = :user_id)
            OR similar_segment_id IN (SELECT segment_id FROM segments WHERE user_id = :user_id)
    """
    result = execute_sql(connection, query, {"user_id": user_id})
    logger.info(f"Deleted similarity data: {result.rowcount} rows affected.")

def chunked(iterable, size=5000):
    """Yield successive chunks from iterable."""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

def save_similarity_data(connection, similarity_data):
    """
    Bulk insert similarity data into the segment_similarity table in chunks.
    """
    if similarity_data.empty:
        logger.info("No similarity data to insert")
        return

    data_to_insert = []
    for index, row in similarity_data.iterrows():
        data_to_insert.append({
            'segment_id': row['segment_id'],
            'similar_segment_id': row['similar_segment_id'],
            'similarity_score': float(row['similarity_score']),
            'rank': int(row['rank'])
        })

    query = text("""
        INSERT INTO segment_similarity (
            segment_id, similar_segment_id, similarity_score, rank
        )
        VALUES (
            :segment_id, :similar_segment_id, :similarity_score, :rank
        )
        ON CONFLICT (segment_id, similar_segment_id) DO UPDATE 
        SET similarity_score = EXCLUDED.similarity_score,
            rank = EXCLUDED.rank,
            calculated_at = CURRENT_TIMESTAMP
    """)

    total_rows = 0
    for chunk in chunked(data_to_insert, size=5000):
        result = connection.execute(query, chunk)
        total_rows += result.rowcount
        logger.info(f"Inserted {total_rows} segment similarity rows.")

    logger.info(f"Saved similarity data: {total_rows} rows affected.")

def get_user_id_from_activity(engine, activity_id):
    try:
        with engine.begin() as connection:
            query = "SELECT athlete_id from activities where id = :activity_id"
            result = fetch_one_sql(connection, query, {"activity_id": activity_id})
            return result[0] if result else None
    except SQLAlchemyError as e:
        raise DatabaseException(f"Database error: {e}")