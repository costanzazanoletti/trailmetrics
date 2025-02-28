import pytest
import pandas as pd
from sqlalchemy import text
from app.database import store_segments, get_raw_activity_streams, create_segments_table, engine

@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """Ensure the test database is properly set up before running tests."""
    with engine.connect() as conn:
        # Ensure the table exists before running tests
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

        # Clean the table before each test
        conn.execute(text("TRUNCATE TABLE segments RESTART IDENTITY CASCADE;"))
        conn.commit()

    yield  # Run the tests

    # Cleanup after tests
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE segments RESTART IDENTITY CASCADE;"))
        conn.commit()


def test_store_segments():
    """Test inserting segments into the database."""
    data = {
        "activity_id": [12345],
        "start_distance": [0.0],
        "end_distance": [100.0],
        "segment_length": [100.0],
        "avg_gradient": [5.0],
        "avg_cadence": [80.0],
        "movement_type": ["run"],
        "type": ["hill"],
        "grade_category": [1.5]
    }
    df = pd.DataFrame(data)

    store_segments(df)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM segments;")).fetchone()
    
    assert result[0] == 1, "Failed to insert segment"

def test_get_raw_activity_streams():
    """Test fetching activity streams from an empty database."""
    activity_id = 12345
    df = get_raw_activity_streams(activity_id)
    assert df.empty, "Expected no results but got data"
