import pytest
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import text
from services.weather_service import process_weather_info
from services.terrain_service import process_terrain_info
from services.segments_service import process_segments
from services.similarity_service import run_similarity_computation
from db.setup import engine 

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
    Tests computing and saving to database the similarity matrix for a given user,
    and verifies that similarity_processed_at is updated correctly.
    """
    user_id = setup_similarity_test_data

    run_similarity_computation(user_id)

    with engine.begin() as conn:
        # Check that similarity data are saved correctly
        result = conn.execute(text("""
            SELECT * FROM segment_similarity 
            WHERE segment_id = 'seg1' OR similar_segment_id = 'seg2'
        """)).fetchall()
        assert result
        assert all('similarity_score' in dict(row._mapping) for row in result)
        assert all('rank' in dict(row._mapping) for row in result)

        # Check that similarity_processed_at was updated only for processable activities
        processed_rows = conn.execute(text("""
            SELECT ast.similarity_processed_at, ast.not_processable
            FROM activity_status_tracker ast
            JOIN activities a ON ast.activity_id = a.id
            WHERE a.athlete_id = :user_id
        """), {"user_id": user_id}).fetchall()

        assert processed_rows
        for row in processed_rows:
            if row.not_processable:
                assert row.similarity_processed_at is None
            else:
                assert row.similarity_processed_at is not None

from services.efficiency_zone_service import calculate_efficiency_zones_for_segments

def test_calculate_efficiency_zones_with_db(set_up, setup_similarity_test_data):
    user_id = setup_similarity_test_data

    run_similarity_computation(user_id)
    calculate_efficiency_zones_for_segments(engine)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT e.segment_id, e.zone_among_similars, e.zone_among_grade_category
            FROM segment_efficiency_zone e
            JOIN segments s ON s.segment_id = e.segment_id
            JOIN activities a ON s.activity_id = a.id
            WHERE a.athlete_id = :user_id
        """), {"user_id": user_id}).fetchall()

    assert result, "No segment efficiency zones were saved"
    for row in result:
        assert row.zone_among_similars in ["very_low", "low", "medium", "high", "very_high"]
        assert row.zone_among_grade_category in ["very_low", "low", "medium", "high", "very_high"]
