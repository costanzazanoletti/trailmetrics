import logging
import logging_setup
from sqlalchemy import text
from app.exceptions import DatabaseException
from sqlalchemy.exc import SQLAlchemyError
from db.setup import engine
from db.core import execute_sql, fetch_one_sql, fetch_all_sql_df

logger = logging.getLogger("app")

def segments_batch_insert_and_update_status(segments_df, activity_id, engine):
    """Batch insert segments and update activity status in transaction using SQLAlchemy."""
    try:
        with engine.begin() as connection:
            query = text("""
                INSERT INTO segments (segment_id, activity_id,  start_distance, end_distance, segment_length,
                    avg_gradient, avg_cadence, movement_type, "type", grade_category,
                    start_lat, start_lng, end_lat, end_lng, start_altitude, end_altitude,
                    start_time, end_time, start_heartrate, end_heartrate, avg_heartrate,
                    avg_speed, elevation_gain, hr_drift, efficiency_score, user_id, 
                    cumulative_ascent, cumulative_descent)
                VALUES (:segment_id, :activity_id, :start_distance, :end_distance, :segment_length,
                        :avg_gradient, :avg_cadence, :movement_type, :type, :grade_category,
                        :start_lat, :start_lng, :end_lat, :end_lng, :start_altitude, :end_altitude,
                        :start_time, :end_time, :start_heartrate, :end_heartrate, :avg_heartrate,
                        :avg_speed, :elevation_gain, :hr_drift, :efficiency_score, :user_id,
                        :cumulative_ascent, :cumulative_descent)
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
                    cumulative_ascent = EXCLUDED.cumulative_ascent,                    
                    cumulative_descent = EXCLUDED.cumulative_descent,                    
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
                    weather_id, 
                    cumulative_ascent,
                    cumulative_descent
                FROM segments
                WHERE user_id = :user_id
            """
    return fetch_all_sql_df(connection, query, {"user_id": user_id})
    
def delete_all_data_by_activity_ids(activity_ids, engine=engine):
    """Delete all segments and activity_status_tracker and similarity data."""
    try:
        with engine.begin() as connection:
            query_similarity = """
                                DELETE FROM segment_similarity
                                WHERE segment_id IN (SELECT segment_id FROM segments WHERE activity_id IN :activity_ids)
                                OR similar_segment_id IN (SELECT segment_id FROM segments WHERE activity_id IN :activity_ids)
                            """
            query_efficiency = """
                                DELETE FROM segment_efficiency_zone
                                WHERE segment_id IN (SELECT segment_id FROM segments WHERE activity_id IN :activity_ids)
                            """
            query_segments = "DELETE FROM segments WHERE activity_id in :activity_ids"
            query_status = "DELETE FROM activity_status_tracker WHERE activity_id in :activity_ids"
            query_weather_progress = "DELETE FROM weather_data_progress WHERE activity_id in :activity_ids"
            execute_sql(connection, query_similarity, {"activity_ids": activity_ids})
            execute_sql(connection, query_efficiency, {"activity_ids": activity_ids})
            execute_sql(connection, query_segments, {"activity_ids": activity_ids})
            execute_sql(connection, query_status, {"activity_ids": activity_ids})
            execute_sql(connection, query_weather_progress, {"activity_ids": activity_ids})
    except SQLAlchemyError as e:
        raise DatabaseException(f"Database error: {e}")
    
