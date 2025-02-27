import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Make sure the .env file exists and is configured correctly.")

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL)

def get_db_connection():
    """Creates and returns a connection to PostgreSQL."""
    return psycopg2.connect(DATABASE_URL)

def get_raw_activity_streams(activity_id):
    """
    Retrieves raw time-series data for a given activity from the database.
    """
    query = """
    SELECT type, data 
    FROM activity_streams
    WHERE activity_id = %s;
    """
    df_streams = pd.read_sql(query, engine, params=(activity_id,))
    return df_streams

def store_segments(segments_df):
    """
    Stores segmented data into the 'segments' table.
    """
    if segments_df.empty:
        print("No segments to store.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO segments (activity_id, start_distance, end_distance, segment_length, avg_gradient,
                          avg_cadence, movement_type, type, grade_category)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    for _, row in segments_df.iterrows():
        cursor.execute(query, (
            row["activity_id"],
            row["start_distance"],
            row["end_distance"],
            row["segment_length"],
            row["avg_gradient"],
            row["avg_cadence"],
            row["movement_type"],
            row["type"],
            row["grade_category"]
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Stored {len(segments_df)} segments in the database.")

def create_segments_table():
    """
    Checks if the 'segments' table exists. If not, creates it.
    """
    check_query = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'segments'
    );
    """
    
    create_query = """
    CREATE TABLE segments (
        id SERIAL PRIMARY KEY,
        activity_id BIGINT NOT NULL,
        start_distance FLOAT NOT NULL,
        end_distance FLOAT NOT NULL,
        segment_length FLOAT NOT NULL,
        avg_gradient FLOAT NOT NULL,
        avg_cadence FLOAT NOT NULL,
        movement_type VARCHAR(20) NOT NULL,
        type VARCHAR(20) NOT NULL,
        grade_category FLOAT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(check_query))
        table_exists = result.scalar()  # Returns True if the table exists, False otherwise

        if not table_exists:
            print("🔍 Table 'segments' not found. Creating it now...")
            conn.execute(text(create_query))
            conn.commit()
            print("'segments' table created successfully.")
        else:
            print("Table 'segments' already exists. No action needed.")



# Checks/creates the table on startup
create_segments_table()