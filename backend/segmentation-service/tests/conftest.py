import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.fixture(scope="session")
def test_database():
    """Fixture to set up a temporary PostgreSQL database for testing."""
    test_db_url = os.getenv("TEST_DATABASE_URL", "postgresql://user:password@localhost/test_db")

    engine = create_engine(test_db_url)
    Session = sessionmaker(bind=engine)

    # Ensure database table is created
    with engine.connect() as conn:
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

    yield engine, Session()

    # Cleanup after tests
    engine.dispose()
