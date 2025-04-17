import pytest
import json
import gzip
import base64
import pandas as pd
from sqlalchemy import text
from database import engine

def dataframe_to_compressed_json(df):
    """Helper function to convert a dataframe into compressed json"""
    json_data = df.to_dict(orient="records")
    json_str = json.dumps(json_data).encode("utf-8")
    compressed_json = gzip.compress(json_str)
    return base64.b64encode(compressed_json).decode("utf-8")

@pytest.fixture
def set_up(autouse=True):
    """Clear all data"""
    print("\nTEST SET UP: Clear all data from database\n")
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM segments"))
        connection.execute(text("DELETE FROM activity_status_tracker"))
        connection.execute(text("DELETE FROM weather_data_progress"))
        connection.execute(text("DELETE FROM segment_similarity"))
        connection.commit()

@pytest.fixture
def create_sample_data():
    """Create sample data for all services"""
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

@pytest.fixture
def setup_similarity_test_data(engine=engine):
    user_id = "9999"  # Use a fixed test ID to clean easily
    with engine.begin() as conn:
        # Insert segments
        conn.execute(text("""
            INSERT INTO segments (
                segment_id, activity_id, user_id, grade_category,
                segment_length, start_distance, start_time, start_altitude,
                elevation_gain, avg_gradient, road_type, surface_type,
                temperature, humidity, wind, weather_id
            ) VALUES 
            ('seg1', 1, :user_id, 1.5, 100, 0, 123456, 10,
             20, 1.5, 'asphalt', 'smooth', 20, 50, 1.8, 100),
            ('seg2', 1, :user_id, 1.5, 120, 100, 789456, 12,
             18, 1.2, 'asphalt', 'smooth', 21, 52, 0, 1)
        """), {"user_id": user_id})
    yield user_id
    # Teardown
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM segment_similarity WHERE segment_id_1 IN ('seg1', 'seg2') OR segment_id_2 IN ('seg1', 'seg2')"))
        conn.execute(text("DELETE FROM segments WHERE user_id = :user_id"), {"user_id": user_id})