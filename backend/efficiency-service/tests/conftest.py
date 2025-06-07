import pytest
import json
import gzip
import base64
import pandas as pd
import numpy as np
import os
import joblib
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from unittest.mock import Mock, MagicMock
from sqlalchemy import text
from db.setup import engine
from utils.models import get_model_paths


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
        'cumulative_ascent': [10, 12],
        'cumulative_descent': [0, 5]
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
    user_id = "9999"
    with engine.begin() as conn:
        # Insert activities
        conn.execute(text("""
            INSERT INTO activities (id, athlete_id)
            VALUES (1, :athlete_id), (2, :athlete_id)
        """), {"athlete_id": user_id})

        # Insert activity_status_tracker with one not_processable
        conn.execute(text("""
            INSERT INTO activity_status_tracker (activity_id, not_processable)
            VALUES 
            (1, false), 
            (2, true)
        """))

        # Insert segments (linked to activity 1)
        conn.execute(text("""
            INSERT INTO segments (
                segment_id, activity_id, user_id, grade_category,
                segment_length, start_distance, start_time, start_altitude,
                elevation_gain, avg_gradient, road_type, surface_type,
                temperature, humidity, wind, weather_id, cumulative_ascent, cumulative_descent,
                efficiency_score
            ) VALUES 
            ('seg1', 1, :user_id, 1.5, 100, 0, 123456, 10,
             20, 1.5, 'asphalt', 'smooth', 20, 50, 1.8, 100, 15, 10, 0.75),
            ('seg2', 1, :user_id, 1.5, 120, 100, 789456, 12,
             18, 1.2, 'asphalt', 'smooth', 21, 52, 0, 1, 10, 5, 0.85)
        """), {"user_id": user_id})

    yield user_id

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM segment_similarity WHERE segment_id IN ('seg1', 'seg2') OR similar_segment_id IN ('seg1', 'seg2')"))
        conn.execute(text("DELETE FROM segments WHERE user_id = :user_id"), {"user_id": user_id})
        conn.execute(text("DELETE FROM activity_status_tracker WHERE activity_id IN (1, 2)"))
        conn.execute(text("DELETE FROM activities WHERE id IN (1, 2)"))
        conn.execute(text("DELETE FROM segment_efficiency_zone WHERE segment_id IN ('seg1', 'seg2')"))

@pytest.fixture
def load_test_message(request):
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, request.param)
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")
    return mock_message

@pytest.fixture
def load_sample_segments(request):
    """Loads a real segments from a JSON file."""
    filename = request.param
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, filename)
    with open(file_path, "r") as file:
        message_data = json.load(file)

    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")
    data = mock_message.value if isinstance(mock_message.value, dict) else json.loads(mock_message.value)
    activity_id = data.get("activityId")
    user_id = data.get("userId")
    is_planned = data.get("isPlanned")
    compressed_segments = data.get("compressedSegments")

    return activity_id, user_id, compressed_segments, is_planned

@pytest.fixture
def mock_engine():
    # Mock the engine that would be passed to the function
    mock_engine = MagicMock()
    return mock_engine

@pytest.fixture
def sample_grade_category_data():
    return np.array([
        [1.0, 2.0, 0.5],
        [1.5, 2.5, 0.6],
        [0.2, 0.1, 1.0],
        [0.3, 0.2, 0.9]
    ])

@pytest.fixture
def sample_segments():
    return pd.DataFrame({
        'segment_id' : ["123-456", "123-789"],
        'grade_category': [0.0, 0.0],
        'segment_length': [10, 20],
        'start_distance': [100, 200],
        'start_time': [3600, 7200],
        'start_altitude': [300, 500],
        'elevation_gain': [100, 200],
        'avg_gradient': [0.05, 0.10],
        'road_type': ['asphalt', 'gravel'],
        'surface_type': ['smooth', 'rough'],
        'temperature': [25, 30],
        'humidity': [60, 70],
        'wind': [5, 10],
        'weather_id': [1, 2]
    })

@pytest.fixture
def sample_df_for_similarity_matrix():
    return pd.DataFrame({
        'segment_id': ["123-456", "123-789", "456-789", "789-123"],
        'grade_category': [0.0, 0.0, 1.0, 1.0],
        'segment_length': [10, 20, 15, 25],
        'start_distance': [100, 200, 150, 250],
        'start_time': [3600, 7200, 5400, 9000],
        'start_altitude': [300, 500, 350, 550],
        'elevation_gain': [100, 200, 120, 220],
        'avg_gradient': [0.05, 0.10, 0.07, 0.12],
        'road_type': ['asphalt', 'gravel', 'asphalt', 'dirt'],
        'surface_type': ['smooth', 'rough', 'smooth', 'rough'],
        'temperature': [25, 30, 27, 32],
        'humidity': [60, 70, 65, 75],
        'wind': [5, 10, 7, 12],
        'weather_id': [100, 200, 100, 300]
    })

# Recommendation
@pytest.fixture
def mock_df_from_csv():
    return pd.read_csv("tests/mock_segments_with_zones.csv")


@pytest.fixture
def dummy_model_files():
    user_id = 28658549

    numeric = ['segment_length', 'avg_gradient', 'start_distance', 'start_altitude',
               'temperature', 'humidity', 'wind', 'cumulative_ascent', 'cumulative_descent']
    categorical = ['grouped_highway', 'grouped_surface']

    preprocessor = ColumnTransformer([
        ("num", Pipeline([
            ("imputer", SimpleImputer(strategy="mean")),
            ("scaler", StandardScaler())
        ]), numeric),
        ("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore"))
        ]), categorical)
    ])

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", DummyRegressor(strategy="mean"))
    ])

    # Fit con dati dummy coerenti
    X_dummy = pd.DataFrame({**{col: [0] for col in numeric}, **{col: ["a"] for col in categorical}})
    y_dummy = [0]
    pipeline.fit(X_dummy, y_dummy)

    model_cad_path, model_spd_path = get_model_paths(user_id)
    os.makedirs(os.path.dirname(model_cad_path), exist_ok=True)
    joblib.dump(pipeline, model_cad_path)
    joblib.dump(pipeline, model_spd_path)

    yield user_id

    for p in [model_cad_path, model_spd_path]:
        if os.path.exists(p):
            os.remove(p)
