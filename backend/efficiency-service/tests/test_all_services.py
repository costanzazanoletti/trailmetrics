import pytest
import json
import os
import gzip
import base64
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from sqlalchemy import text
from app.weather_service import process_weather_info
from app.terrain_service import process_terrain_info
from app.segments_service import process_segments
from app.exceptions import DatabaseException
from database import delete_all_data, engine  


@pytest.fixture
def set_up(autouse=True):
    print("\nTEST SET UP: Clear all data from database\n")
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM segments"))
        connection.execute(text("DELETE FROM activity_status_tracker"))
        connection.execute(text("DELETE FROM weather_data_progress"))
        connection.execute(text("DELETE FROM segment_similarity"))
        connection.commit()


def dataframe_to_compressed_json(df):
    json_data = df.to_dict(orient="records")
    json_str = json.dumps(json_data).encode("utf-8")
    compressed_json = gzip.compress(json_str)
    return base64.b64encode(compressed_json).decode("utf-8")


@pytest.fixture
def create_sample_data():
    weather_data_1 = {
        'segment_id': ["987-1"],
        'lat': [46.0807],
        'lon': [8.2799],
        'dt': [1738159835],
        'temp': [9.74],
        'feels_like': [8.74],
        'humidity': [61],
        'wind': [1.03],
        'weather_id': [803],
        'weather_main': ['Clouds'],
        'weather_description': ['broken clouds'],
    }

    weather_data_2 = {
        'segment_id': ["987-2"],
        'lat': [46.1122],
        'lon': [8.2801],
        'dt': [1738159999],
        'temp': [9.91],
        'feels_like': [9.11],
        'humidity': [61],
        'wind': [1.05],
        'weather_id': [501],
        'weather_main': ['Rain'],
        'weather_description': ['light rain'],
    }

    terrain_data = {
        'segment_id': ["987-1", "987-2"],
        'highway': ["cycleway", "secondary"],
        'surface': ["asphalt", None]
    }

    segments_data = {
        "activity_id": [987, 987],
        "start_distance": [0.0, 50.0],
        "end_distance": [50.0, 100.0],
        "segment_length": [50.0, 50.0],
        "avg_gradient": [-5.0, 2.0],
        "avg_cadence": [80, 85],
        "movement_type": ["run", "walk"],
        "type": ["downhill", "uphill"],
        "grade_category": [-5, 2],
        "start_lat": [46.1, 46.2],
        "start_lng": [8.4, 8.5],
        "end_lat": [46.15, 46.25],
        "end_lng": [8.45, 8.55],
        "start_altitude": [820, 810],
        "end_altitude": [810, 830],
        "start_time": [0, 100],
        "end_time": [100, 200],
        "start_heartrate": [100, 120],
        "end_heartrate": [120, 130],
        "avg_heartrate": [110.2, 120.2],
        'segment_id': ["987-1", "987-2"],
    }

    activity_id = 987
    user_id = "123"
    group_id = ["1_2", "2_2"]
    compressed_weather_info = [dataframe_to_compressed_json(pd.DataFrame(weather_data_1)),
                               dataframe_to_compressed_json(pd.DataFrame(weather_data_2))]
    compressed_terrain_info = dataframe_to_compressed_json(pd.DataFrame(terrain_data))
    compressed_segments_info = dataframe_to_compressed_json(pd.DataFrame(segments_data))
    return activity_id, user_id, group_id, compressed_weather_info, compressed_terrain_info, compressed_segments_info


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