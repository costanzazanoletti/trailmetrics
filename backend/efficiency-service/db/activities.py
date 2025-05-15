import logging
import logging_setup
from exceptions.exceptions import DatabaseException
from sqlalchemy.exc import SQLAlchemyError
from db.setup import engine
from db.core import execute_sql, fetch_one_sql

logger = logging.getLogger("app")

def insert_not_processable_activity_status(activity_id, engine):
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

def get_user_id_from_activity(engine, activity_id):
    try:
        with engine.begin() as connection:
            query = "SELECT athlete_id from activities where id = :activity_id"
            result = fetch_one_sql(connection, query, {"activity_id": activity_id})
            return str(result[0]) if result else None
    except SQLAlchemyError as e:
        raise DatabaseException(f"Database error: {e}")
    
