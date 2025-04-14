import pytest
import json
import os
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import base64
from datetime import datetime, timezone
from sqlalchemy import text
from app.segments_service import process_segments, calculate_metrics, compute_efficiency_score
from app.exceptions import DatabaseException
from database import engine 

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
    file_path = os.path.join(base_dir, 'mock_segmentation.json')
    with open(file_path, "r") as file:
        message_data = json.load(file)

    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")
    data = mock_message.value if isinstance(mock_message.value, dict) else json.loads(mock_message.value)
    activity_id = data.get("activityId")
    compressed_segments = data.get("compressedSegments")

    return activity_id, compressed_segments

def test_process_segments(load_sample_segments, set_up):
    """
    Tests process_segments_message.
    Stores data into the test Database.
    """
    # Load sample data
    activity_id, compressed_segments = load_sample_segments

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        # Check the number of segments before execution
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Call process_segments (assuming it now uses the engine)
        process_segments(activity_id, compressed_segments, engine=engine)

        # Check the number of segments after execution
        final_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Check that activity_status_tracker has been updated
        segment_status = connection.execute(
            text("SELECT segment_status FROM activity_status_tracker WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Assertion
        expected_rows = 193
        assert (final_count - initial_count) == expected_rows, "No segments were inserted into the database"
        assert segment_status is True

def test_process_segments_with_database_exception(load_sample_segments, set_up):
    """Tests that process_segments_message doesn't store any data when it handles a DatabaseException."""
    with patch('app.segments_service.segments_batch_insert_and_update_status') as mock_store_segments:
        # Load sample data
        activity_id, compressed_segments = load_sample_segments

        # Configure mock to raise a DatabaseException
        mock_store_segments.side_effect = DatabaseException("Database error occurred while inserting segments.")

        # Use SQLAlchemy connection
        with engine.connect() as connection:
            # Check the number of segments before execution
            initial_count = connection.execute(
                text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
                {"activity_id": activity_id}
            ).scalar_one()

            # Call process_segments (assuming it now uses the engine and handles exceptions)
            process_segments(activity_id, compressed_segments, engine=engine)

            # Check the number of segments after execution
            final_count = connection.execute(
                text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
                {"activity_id": activity_id}
            ).scalar_one()

            # Assertion
            assert final_count == initial_count, "Segments were inserted into the database"

def test_process_segments_for_existing_activity(load_sample_segments, set_up):
    """
    Tests process_segments_message when the activity has already been processed.
    """
    # Load sample data
    activity_id, compressed_segments = load_sample_segments

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        # Call process_segments (first time)
        process_segments(activity_id, compressed_segments, engine=engine)

        # Check the number of segments before the second call
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Call process_segments a second time
        process_segments(activity_id, compressed_segments, engine=engine)

        # Check the number of segments after the second call
        final_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Assertion
        assert final_count == initial_count, "Segments were inserted into the database on the second call"

def test_calculate_metrics():
    # Sample data
    segment = {
        "segment_length": 100,
        "start_time": 0,
        "end_time": 45,
        "start_altitude": 100,
        "end_altitude": 110,
        "start_heartrate": 120,
        "end_heartrate": 130
    }
    segment_df = pd.DataFrame([segment])

    # Call function
    result_segment = calculate_metrics(segment_df.iloc[0])

    # Assertions
    expected_avg_speed = 100/45
    assert np.isclose(result_segment["avg_speed"], expected_avg_speed), f"Expected {expected_avg_speed}, got {result_segment['avg_speed']}"
    expected_elevation_gain = 10
    assert np.isclose(result_segment["elevation_gain"], expected_elevation_gain), f"Expected {expected_elevation_gain}, got {result_segment['elevation_gain']}"
    expected_hr_drift = (130  - 120) / 120
    assert np.isclose(result_segment["hr_drift"], expected_hr_drift), f"Expected {expected_hr_drift}, got {result_segment['hr_drift']}"

def test_compute_efficiency_score():
    # Sample data
    data = {
        "avg_speed": [1, 1, 1],
        "elevation_gain": [10, 10, -10],
        "segment_length": [100, 100, 100],
        "avg_heartrate": [150, 150, 150],
        "hr_drift": [0.5, 0.0, -0.5]
    }

    df = pd.DataFrame(data)

    # Paramters
    s = 10.0
    k = 1
    m = 1

    result_df = compute_efficiency_score(df, s, k, m)

    print(result_df)