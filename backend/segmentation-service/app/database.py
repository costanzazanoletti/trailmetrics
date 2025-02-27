import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
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
