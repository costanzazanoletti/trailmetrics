import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch
from sqlalchemy import text
from app.weather_service import process_weather_info
from app.exceptions import DatabaseException
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
def load_sample_weather():
    """Loads sample weather data from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'mock_weather.json')
    with open(file_path, "r") as file:
        message_data = json.load(file)

    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")
    data = mock_message.value if isinstance(mock_message.value, dict) else json.loads(mock_message.value)
    activity_id = data.get("activityId")
    group_id = data.get("groupId")
    compressed_weather_info = data.get("compressedWeatherInfo")
    total_groups = data.get("totalGroups")

    return activity_id, group_id, compressed_weather_info, total_groups

def test_process_weather_info(load_sample_weather, set_up):
    """
    Tests process_weather_info with sample data.
    Stores data into the test Database.
    """
    # Load sample data
    activity_id, group_id, compressed_weather_info, total_groups = load_sample_weather

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        # Check the number of segments before execution
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id AND temperature IS NOT NULL"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Call process_weather_info (assuming it now uses the engine)
        process_weather_info(activity_id, group_id, compressed_weather_info, engine=engine)

        # Check the number of segments after execution
        final_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id AND temperature IS NOT NULL"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Check that weather_status in activity_status_tracker might be updated
        weather_status = connection.execute(
            text("SELECT weather_status FROM activity_status_tracker WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one_or_none()  # Use scalar_one_or_none in case the row doesn't exist yet

        # Assertion
        expected_rows = 3  # mock_weather.json has info for 3 segments
        assert (final_count - initial_count) == expected_rows, "Weather info was not inserted/updated"
        if total_groups == '1_1':  # Assuming '1_1' means all groups processed
            assert weather_status is True
        elif weather_status is not None:
            assert weather_status is False # If not all groups, status should remain False or be set to False

@patch('app.weather_service.weather_batch_insert_and_update_status')
def test_process_weather_info_with_database_exception(mock_store_weather, load_sample_weather, set_up):
    """Tests that process_weather_info handles DatabaseException gracefully."""
    
    # Load sample data
    activity_id, group_id, compressed_weather_info, total_groups = load_sample_weather

    # Configure mock to raise a DatabaseException
    mock_store_weather.side_effect = DatabaseException("Database error occurred while saving weather data.")

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        # Check the number of segments before execution
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id AND temperature IS NOT NULL"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Call process_weather_info
        process_weather_info(activity_id, group_id, compressed_weather_info, engine=engine)

        # Check the number of segments after execution
        final_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id AND temperature IS NOT NULL"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Check activity_status_tracker
        weather_status = connection.execute(
            text("SELECT weather_status FROM activity_status_tracker WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one_or_none()

        # Assertion
        assert final_count == initial_count, "Weather info was inserted despite the exception"
        if weather_status is not None:
            assert weather_status is False
