import pytest
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from app.database import store_segments, get_raw_activity_streams, create_segments_table

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def test_database():
    """Fixture to set up a temporary PostgreSQL database for testing."""
    test_db_url = os.getenv("TEST_DATABASE_URL")

    engine = create_engine(test_db_url)
    Session = sessionmaker(bind=engine)

    # Drop and recreate the table to ensure fresh schema
    with engine.connect() as conn: 
        conn.execute(text("DROP TABLE IF EXISTS segments CASCADE;"))   
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS segments (
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
                start_lat FLOAT NOT NULL,
                start_lng FLOAT NOT NULL,
                end_lat FLOAT NOT NULL,
                end_lng FLOAT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()


    yield engine, Session()

    # Cleanup after tests
    engine.dispose()

@pytest.fixture(scope="function", autouse=True)
def setup_test_database(test_database):
    """Ensure the test database is properly set up before running tests."""
    engine, _ = test_database

    with engine.connect() as conn:
        # Clean the table before each test
        conn.execute(text("TRUNCATE TABLE segments RESTART IDENTITY CASCADE;"))
        conn.commit()

    yield  # Run the tests

    # Cleanup after tests
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE segments RESTART IDENTITY CASCADE;"))
        conn.commit()


def test_store_segments(test_database):
    """Test inserting segments into the database."""
    engine, _ = test_database
    assert engine is not None, "Database engine is not initialized"
    
    data = {
        "activity_id": [12345],
        "start_distance": [1.0],
        "end_distance": [4.7],
        "segment_length": [11.60],
        "avg_gradient": [2.6],
        "avg_cadence": [59.6],
        "movement_type": ["walking"],
        "type": ["uphill"],
        "grade_category": [2.5],
        "start_lat": [46.142836],
        "start_lng": [8.469562],
        "end_lat": [46.142853],
        "end_lng": [8.469612]
    }
    df = pd.DataFrame(data)

    store_segments(df)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM segments;")).fetchone()
    

    assert result is not None, "Segment not found in database"
    assert result[0] == 1.0, "Incorrect start distance"

