import os
import sys
import logging
import logging_setup
from sqlalchemy import create_engine, text
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

engine = create_engine(DATABASE_URL)

def get_db_engine():
    """Returns the SQLAlchemy engine (connection is handled within the function)."""
    return engine

def execute_sql(query, params=None):
    """Helper function to execute SQL using SQLAlchemy."""
    conn = engine.connect()
    try:
        conn.execute(text(query), params)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise DatabaseException(f"Database error: {e}")
    finally:
        conn.close()

def execute_sql(connection, query, params=None):
    """Helper function to execute SQL using SQLAlchemy with a provided connection."""
    try:
        connection.execute(text(query), params)
    except Exception as e:
        raise DatabaseException(f"Database error: {e}")

def fetch_one_sql(connection, query, params=None):
    """Helper function to fetch one result using SQLAlchemy with a provided connection."""
    try:
        result = connection.execute(text(query), params).fetchone()
        return result
    except Exception as e:
        raise DatabaseException(f"Database error: {e}")

def fetch_all_sql(connection, query, params=None):
    """Helper function to fetch all results using SQLAlchemy with a provided connection."""
    try:
        result = connection.execute(text(query), params).fetchall()
        return result
    except Exception as e:
        raise DatabaseException(f"Database error: {e}")

def delete_all_data(engine):
    """Delete all segments and activity_status_tracker using SQLAlchemy."""
    with engine.begin() as connection:
        query_segments = "DELETE FROM segments WHERE activity_id IS NOT NULL"
        query_status = "DELETE FROM activity_status_tracker WHERE activity_id IS NOT NULL"
        query_weather_progress = "DELETE FROM weather_data_progress WHERE activity_id IS NOT NULL"
        execute_sql(connection, query_segments)
        execute_sql(connection, query_status)
        execute_sql(connection, query_weather_progress)

def segments_batch_insert_and_update_status(segments_df, activity_id, engine):
    """Batch insert segments and update activity status in transaction using SQLAlchemy."""
    
    try:
        with engine.begin() as connection:
            upsert_query = text("""
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
            connection.execute(upsert_query, segments_data)
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
            connection.commit()  # Commit within the transaction context
    except SQLAlchemyError as e:
        connection.rollback()
        raise DatabaseException(f"An error occurred: {e}")


def terrain_batch_insert_and_update_status(segments_df, activity_id, engine):
    """Batch insert segment terrain info and update activity status in transaction using SQLAlchemy."""
    try:
        with engine.begin() as connection:  # Use context manager for transaction
            upsert_query = text("""
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
                connection.execute(upsert_query, row)

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
            upsert_weather_query = text("""
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
                connection.execute(upsert_weather_query, record)

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

def save_similarity_matrix(similarity_data, engine):
    """
    Saves the computed similarity data to the segment_similarity table using SQLAlchemy.
    """
    if similarity_data:
        try:
            with engine.connect() as connection: # This one is okay as it's a standalone operation
                stmt = text("""
                    INSERT INTO segment_similarity (segment_id_1, segment_id_2, similarity_score)
                    VALUES (:segment_id_1, :segment_id_2, :similarity_score)
                    ON CONFLICT (segment_id_1, segment_id_2) DO UPDATE
                    SET similarity_score = EXCLUDED.similarity_score,
                        calculated_at = DEFAULT
                """)
                connection.execute(
                    stmt,
                    similarity_data
                )
                connection.commit()
            logger.info(f"Successfully saved {len(similarity_data)} similarity scores to the database.")
        except Exception as e:
            logger.error(f"Error saving similarity matrix to database: {e}")
            raise DatabaseException(f"Error saving similarity matrix: {e}")
    else:
        logger.info("No similarity scores to save.")