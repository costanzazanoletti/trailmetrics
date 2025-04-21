import pytest
import json
import os
import gzip
import base64
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import text
from app.weather_service import process_weather_info
from app.terrain_service import process_terrain_info
from app.segments_service import process_segments
from app.similarity_service import run_similarity_computation
from app.exceptions import DatabaseException
from database import engine  

def test_process_segments_terrain_weather(set_up, create_sample_data):
    """
    Tests processing the same activity.
    Stores data into the test Database and updates the activity_status_tracker.
    """
    activity_id, user_id, group_id, compressed_weather_info, compressed_terrain_info, compressed_segments_info = create_sample_data

    # Check the number of segments before execution
    with engine.connect() as connection:
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Call all services
        process_segments(activity_id, user_id, compressed_segments_info, engine=engine)
        process_terrain_info(activity_id, compressed_terrain_info, engine=engine)  
        process_weather_info(activity_id, group_id[0], compressed_weather_info[0], engine=engine)  
        process_weather_info(activity_id, group_id[1], compressed_weather_info[1], engine=engine)  

        # Check the number of segments after execution
        final_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Check activity_status_tracker
        status_result = connection.execute(
            text("""
                SELECT segment_status, terrain_status, weather_status
                FROM activity_status_tracker
                WHERE activity_id = :activity_id
            """),
            {"activity_id": activity_id}
        ).fetchone()

    # Assertion
    expected_rows = 2
    assert (final_count - initial_count) == expected_rows, "Segments were not inserted into the database"
    assert status_result is not None, f"No result found for activity_id {activity_id}"
    assert all(status == True for status in status_result), "One or more statuses are False"

def test_process_weather_segments_terrain_weather(set_up, create_sample_data):
    """
    Tests processing the same activity with a different order of service calls.
    Stores data into the test Database and updates the activity_status_tracker.
    """
    activity_id, user_id, group_id, compressed_weather_info, compressed_terrain_info, compressed_segments_info = create_sample_data

    # Check the number of segments before execution
    with engine.connect() as connection:
        initial_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Call all services in a different order
        process_weather_info(activity_id, group_id[0], compressed_weather_info[0], engine=engine) 
        process_segments(activity_id, user_id, compressed_segments_info, engine=engine)
        process_terrain_info(activity_id, compressed_terrain_info, engine=engine)
        process_weather_info(activity_id, group_id[1], compressed_weather_info[1], engine=engine) 

        # Check the number of segments after execution
        final_count = connection.execute(
            text("SELECT COUNT(*) FROM segments WHERE activity_id = :activity_id"),
            {"activity_id": activity_id}
        ).scalar_one()

        # Check activity_status_tracker
        status_result = connection.execute(
            text("""
                SELECT segment_status, terrain_status, weather_status
                FROM activity_status_tracker
                WHERE activity_id = :activity_id
            """),
            {"activity_id": activity_id}
        ).fetchone()

    # Assertion
    expected_rows = 2
    assert (final_count - initial_count) == expected_rows, "Segments were not inserted into the database"
    assert status_result is not None, f"No result found for activity_id {activity_id}"
    assert all(status == True for status in status_result), "One or more statuses are False"

def test_run_similarity_computation_with_db(set_up, setup_similarity_test_data):
    """
    Tests computing and saving to database the similarity matrix for a given user.
    """
    user_id = setup_similarity_test_data

    run_similarity_computation(user_id)

    with engine.begin() as conn:
        result = conn.execute(text("SELECT * FROM segment_similarity WHERE segment_id = 'seg1' OR similar_segment_id = 'seg2'")).fetchall()
        assert result  # Make sure similarity was inserted
        assert all('similarity_score' in dict(row._mapping) for row in result)
        assert all('rank' in dict(row._mapping) for row in result)