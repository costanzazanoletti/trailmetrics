import pytest
import json
import os
from unittest.mock import Mock, patch
import base64
from sqlalchemy import text
from services.terrain_service import process_terrain_info
from exceptions.exceptions import DatabaseException
from db.setup import engine  

@pytest.fixture
def set_up(autouse=True):
    print("\nTEST SET UP: Clear all data from database\n")
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM segments"))
        connection.execute(text("DELETE FROM activity_status_tracker"))
        connection.execute(text("DELETE FROM weather_data_progress"))
        connection.execute(text("DELETE FROM segment_similarity"))
        connection.commit()

@pytest.fixture
def load_sample_segments():
    """Loads a real segments from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'mock_terrain.json')
    with open(file_path, "r") as file:
        message_data = json.load(file)

    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")
    data = mock_message.value if isinstance(mock_message.value, dict) else json.loads(mock_message.value)
    activity_id = data.get("activityId")
    compressed_terrain_info = data.get("compressedTerrainInfo")

    return activity_id, compressed_terrain_info

def test_process_terrain_info(load_sample_segments, set_up):
    """
    Tests process_terrain_info with a real Kafka message.
    Stores data into the test Database.
    """
    # Load sample data
    activity_id, compressed_terrain_info = load_sample_segments

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        # Check the number of segments before execution
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Call process_terrain_info (assuming it now uses the engine)
        process_terrain_info(activity_id, compressed_terrain_info, engine=engine)

        # Check the number of segments after execution
        final_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Check that activity_status_tracker has been updated
        terrain_status = connection.execute(
            text("SELECT terrain_status FROM activity_status_tracker WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Assertion
        expected_rows = 193
        assert (final_count - initial_count) == expected_rows, "No segments were inserted into the database"
        assert terrain_status is True

@patch('services.terrain_service.terrain_batch_insert_and_update_status')
def test_process_terrain_info_with_database_exception(mock_store_segments, load_sample_segments, set_up):
    """Tests that process_terrain_info doesn't store any data when it handles a DatabaseException."""
    # Load sample data
    activity_id, compressed_terrain_info = load_sample_segments

    # Configure mock to raise a DatabaseException
    mock_store_segments.side_effect = DatabaseException("Database error occurred while inserting terrain info.")

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        process_terrain_info(activity_id, compressed_terrain_info, engine=engine)

        final_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        assert final_count == initial_count, "Segments with terrain info were inserted into the database"