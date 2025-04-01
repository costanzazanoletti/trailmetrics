import os
import sys
import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
import numpy as np
import logging
import logging_setup
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from app.exceptions import DatabaseException

logger = logging.getLogger("app")
# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# If test mode use test database
if "pytest" in sys.modules:
    DATABASE_URL = os.getenv("TEST_DATABASE_URL", DATABASE_URL)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Make sure the .env file exists and is configured correctly.")

print(f"Database URL: {DATABASE_URL}")

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL)

def get_db_connection():
    """Creates and returns a connection to PostgreSQL."""
    return psycopg2.connect(DATABASE_URL)

def convert_values_to_python_native(data):
    """
    Convert single numpy values in Python native (int, float).
    """
    if isinstance(data, np.int64):
        return int(data) 
    elif isinstance(data, np.float64):
        return float(data)  
    return data  

def segments_batch_insert_and_update_status(segments_df, activity_id):
    """Batch insert segments and update activity status in transaction."""
    # Prepare the db connection
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
               
        # SQL query for batch insert or update segments (upsert)
        upsert_query = """
        INSERT INTO segments (activity_id, start_distance, end_distance, segment_length, 
            avg_gradient, avg_cadence, movement_type, "type", grade_category, 
            start_lat, start_lng, end_lat, end_lng, start_altitude, end_altitude, 
            start_time, end_time, start_heartrate, end_heartrate, avg_heartrate, segment_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            last_updated = CURRENT_TIMESTAMP
        """

        # Convert the DataFrame in a list of tuples
        segments_data = [
            tuple(convert_values_to_python_native(x) for x in row) 
            for row in segments_df.to_records(index=False)
        ]
        # Verifica le colonne nel DataFrame
        logger.info(f"Columns in DataFrame: {segments_df.columns.tolist()}")

        # Execute batch insert
        execute_batch(cursor, upsert_query, segments_data)
        
        logger.info("\nExecuted segments batch store\n")

        update_status_query = f"""
        INSERT into activity_status_tracker(activity_id, segment_status)
        VALUES (%s, TRUE)
        ON CONFLICT (activity_id)
        DO UPDATE
        SET 
            segment_status = TRUE, 
            last_updated = CURRENT_TIMESTAMP;
        """
        
        cursor.execute(update_status_query, (activity_id,))

        # Complete the transaction
        conn.commit()

    except Exception as e:
        # If there is an error, rollback
        conn.rollback()
        raise DatabaseException(f"An error occurred {e}")
    
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()
