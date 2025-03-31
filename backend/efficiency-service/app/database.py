import os
import sys
import psycopg2
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

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


def check_segments_table():
    """
    Checks if the 'segments' table exists.
    """
    check_query = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'segments'
    );
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(check_query))
        conn.commit()
        table_exists = result.scalar()  # Returns True if the table exists, False otherwise

        if not table_exists:
            print("Table 'segments' not found.")
        else:
            print("Table 'segments' exists.")

