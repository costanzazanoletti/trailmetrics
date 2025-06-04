import pytest
import json
import os
import pandas as pd
import numpy as np
from unittest.mock import patch
from sqlalchemy import text
from services.segments_service import process_segments, calculate_metrics, compute_efficiency_score, process_deleted_activities
from exceptions.exceptions import DatabaseException
from db.setup import engine
from db.core import execute_sql, fetch_one_sql

@pytest.mark.parametrize("load_sample_segments", ["mock_segmentation.json"], indirect=True)
def test_process_segments(load_sample_segments, set_up):
    """
    Tests process_segments_message.
    Stores data into the test Database.
    """
    # Load sample data
    activity_id, user_id, compressed_segments, is_planned = load_sample_segments

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        # Check the number of segments before execution
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Call process_segments (assuming it now uses the engine)
        process_segments(activity_id, is_planned, user_id, compressed_segments, engine=engine)

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

@pytest.mark.parametrize("load_sample_segments", ["mock_segmentation.json"], indirect=True)
@patch('services.segments_service.segments_batch_insert_and_update_status')
def test_process_segments_with_database_exception(mock_store_segments, load_sample_segments, set_up):
    """Tests that process_segments_message doesn't store any data when it handles a DatabaseException."""
    # Load sample data
    activity_id, user_id, compressed_segments, is_planned = load_sample_segments

    # Configure mock to raise a DatabaseException
    mock_store_segments.side_effect = DatabaseException("Database error occurred while inserting segments.")

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        process_segments(activity_id, is_planned, user_id, compressed_segments, engine=engine)

        final_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        assert final_count == initial_count, "Segments were inserted into the database"

@pytest.mark.parametrize("load_sample_segments", ["mock_segmentation.json"], indirect=True)
def test_process_segments_for_existing_activity(load_sample_segments, set_up):
    """
    Tests process_segments_message when the activity has already been processed.
    """
    # Load sample data
    activity_id, user_id, compressed_segments, is_planned = load_sample_segments

    # Use SQLAlchemy connection
    with engine.connect() as connection:
        # Call process_segments (first time)
        process_segments(activity_id, is_planned, user_id, compressed_segments, engine=engine)

        # Check the number of segments before the second call
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Call process_segments a second time
        process_segments(activity_id, is_planned, user_id, compressed_segments, engine=engine)

        # Check the number of segments after the second call
        final_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Assertion
        assert final_count == initial_count, "Segments were inserted into the database on the second call"

def test_calculate_metrics():
    # Case 1: all values present
    segment_full = {
        "segment_length": 100,
        "start_time": 0,
        "end_time": 45,
        "start_altitude": 100,
        "end_altitude": 110,
        "start_heartrate": 120,
        "end_heartrate": 130
    }
    df_full = pd.DataFrame([segment_full])
    result_full = calculate_metrics(df_full.iloc[0])

    assert np.isclose(result_full["avg_speed"], 100 / 45)
    assert np.isclose(result_full["elevation_gain"], 10)
    assert np.isclose(result_full["hr_drift"], 10)
    assert np.isclose(result_full["avg_elev_speed"], 10 / 45)
    assert result_full["time"] == 45

def test_compute_efficiency_score():
    # Sample data
    data = {
        "segment_length": [100, 200, 250],
        "start_time": [0, 60, 120],
        "end_time": [60, 120, 180],
        "start_altitude": [100, 110, 200],
        "end_altitude": [110, 200, 250],
        "start_heartrate": [120, 130, 120],
        "end_heartrate": [130, 120, 125],
        "avg_heartrate": [125.5, 128.0, 123.9]
    }

    df = pd.DataFrame(data)

    # Paramters
    SF = 1
    EW = 0.1
    DW = 0.5

    result_df = compute_efficiency_score(df, SF, EW, DW)

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

@pytest.mark.parametrize("load_sample_segments", ["mock_planned_message.json"], indirect=True)
def test_process_planned_segments(load_sample_segments, set_up):
    """
    Tests process_segments_message for planned activity.
    Stores data into the test Database.
    """
    # Load sample data
    activity_id, user_id, compressed_segments, is_planned = load_sample_segments
    initial_count = 0
    final_count = 0
    
    # Check database initial status
    with engine.begin() as connection:
        # Check the number of segments before execution
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()
        print(f"INITIAL COUNT {initial_count}")

    # Call process_segments (assuming it now uses the engine)
    process_segments(activity_id, is_planned, user_id, compressed_segments, engine=engine)
    
    # Check database final status
    with engine.begin() as connection:
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
    expected_rows = 43 # segments in mock file
    assert (final_count - initial_count) == expected_rows, "No segments were inserted into the database"
    assert segment_status is True    