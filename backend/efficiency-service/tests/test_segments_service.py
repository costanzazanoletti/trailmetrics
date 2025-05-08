import pytest
import json
import os
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import base64
from datetime import datetime, timezone
from sqlalchemy import text
from app.segments_service import process_segments, calculate_metrics, compute_efficiency_score, process_deleted_activities
from app.exceptions import DatabaseException
from database import engine, execute_sql, delete_all_data, fetch_one_sql  

def test_process_segments(load_sample_segments, set_up):
    """
    Tests process_segments_message.
    Stores data into the test Database.
    """
    # Load sample data
    activity_id, user_id, compressed_segments = load_sample_segments

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        # Check the number of segments before execution
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Call process_segments (assuming it now uses the engine)
        process_segments(activity_id, user_id, compressed_segments, engine=engine)

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
        expected_rows = 137
        assert (final_count - initial_count) == expected_rows, "No segments were inserted into the database"
        assert segment_status is True

@patch('app.segments_service.segments_batch_insert_and_update_status')
def test_process_segments_with_database_exception(mock_store_segments, load_sample_segments, set_up):
    """Tests that process_segments_message doesn't store any data when it handles a DatabaseException."""
    # Load sample data
    activity_id, user_id, compressed_segments = load_sample_segments

    # Configure mock to raise a DatabaseException
    mock_store_segments.side_effect = DatabaseException("Database error occurred while inserting segments.")

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        process_segments(activity_id, user_id, compressed_segments, engine=engine)

        final_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        assert final_count == initial_count, "Segments were inserted into the database"

def test_process_segments_for_existing_activity(load_sample_segments, set_up):
    """
    Tests process_segments_message when the activity has already been processed.
    """
    # Load sample data
    activity_id, user_id, compressed_segments = load_sample_segments

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        # Call process_segments (first time)
        process_segments(activity_id, user_id, compressed_segments, engine=engine)

        # Check the number of segments before the second call
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Call process_segments a second time
        process_segments(activity_id, user_id, compressed_segments, engine=engine)

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

def insert_test_data(activity_ids):
    """Helper function to insert activity data"""
    with engine.connect() as connection:
        for activity_id in activity_ids:
            execute_sql(connection, "INSERT INTO segments (activity_id, segment_id) VALUES (:activity_id, :segment_id)", {"activity_id": activity_id, "segment_id": (str(activity_id) + "-1")})
            execute_sql(connection, "INSERT INTO segments (activity_id, segment_id) VALUES (:activity_id, :segment_id)", {"activity_id": activity_id, "segment_id": (str(activity_id) + "-2")})
                       
            execute_sql(connection, """
                INSERT INTO segment_similarity (segment_id, similar_segment_id, similarity_score, rank)
                VALUES (
                    (SELECT segment_id FROM segments WHERE activity_id = :activity_id LIMIT 1),
                    (SELECT segment_id FROM segments WHERE activity_id = :activity_id ORDER BY segment_id DESC LIMIT 1),
                    0.8, 1
                )
            """, {"activity_id": activity_id})
            execute_sql(connection, "INSERT INTO activity_status_tracker (activity_id) VALUES (:activity_id)", {"activity_id": activity_id})
            execute_sql(connection, "INSERT INTO weather_data_progress (activity_id, group_id, total_groups) VALUES (:activity_id, :group_id, :total_groups)", {"activity_id": activity_id, "group_id": "1_1", "total_groups": 1})
        connection.commit()

def test_success_process_deleted_activities(set_up):
    """
    Tests process_deleted_activities when the activity has already been processed.
    """
    # Prepare test data
    user_id = 123
    deleted_activity_ids = [100, 200]
    insert_test_data(deleted_activity_ids)

    # Call the function
    process_deleted_activities(user_id, deleted_activity_ids)

    # Assertions
    with engine.connect() as connection:
            segment_count = fetch_one_sql(connection, "SELECT COUNT(*) FROM segments WHERE activity_id IN :ids", {"ids": deleted_activity_ids})
            similarity_count = fetch_one_sql(connection, """
                SELECT COUNT(*) FROM segment_similarity
                WHERE segment_id IN (SELECT segment_id FROM segments WHERE activity_id IN :ids)
                OR similar_segment_id IN (SELECT segment_id FROM segments WHERE activity_id IN :ids)
            """, {"ids": deleted_activity_ids})
            status_count = fetch_one_sql(connection, "SELECT COUNT(*) FROM activity_status_tracker WHERE activity_id IN :ids", {"ids": deleted_activity_ids})
            weather_progress_count = fetch_one_sql(connection, "SELECT COUNT(*) FROM weather_data_progress WHERE activity_id IN :ids", {"ids": deleted_activity_ids})

            assert segment_count[0] == 0
            assert similarity_count[0] == 0
            assert status_count[0] == 0
            assert weather_progress_count[0] == 0
    