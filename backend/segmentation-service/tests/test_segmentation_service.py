import pytest
import pandas as pd
import numpy as np
import logging
import logging_setup
from haversine import haversine, Unit
import json
import base64
import gzip
from app.segmentation_service import (
    preprocess_streams, 
    create_segments, 
    segment_activity, 
    parse_kafka_stream,
    segment_planned_activity,
    parse_planned_activity
    )

# Setup logging
logger = logging.getLogger("app")

def test_parse_kafka_stream(sample_compressed_stream):
    """
    Tests parsing of a Kafka stream into a DataFrame.
    """
    activity_id = 12345
    df = parse_kafka_stream(sample_compressed_stream, activity_id)
    
    assert not df.empty, "Parsed DataFrame should not be empty"
    assert "latlng" in df.columns, "Missing 'latlng' column"
    assert "distance" in df.columns, "Missing 'distance' column"

def test_segment_activity(sample_compressed_stream):
    """
    Tests segment_activity by providing a sample compressed stream and validating the result.
    """
    activity_id = 12345
    segments_df = segment_activity(activity_id, sample_compressed_stream)

    assert isinstance(segments_df, pd.DataFrame), "Output should be a pandas DataFrame"
    assert not segments_df.empty, "Segmentation should produce at least one segment"

    expected_columns = {
        "activity_id", "start_distance", "end_distance", "segment_length", 
        "avg_gradient", "avg_cadence", "movement_type", "type", "grade_category",
        "start_lat", "start_lng", "end_lat", "end_lng", "start_altitude", "end_altitude",
        "start_time", "end_time", "start_heartrate", "end_heartrate", "avg_heartrate",
        "cumulative_ascent", "cumulative_descent"
    }

    assert expected_columns.issubset(set(segments_df.columns)), \
        f"Missing expected columns: {expected_columns - set(segments_df.columns)}"

    print("Segments created by segment_activity:")
    print(segments_df.head())

def test_preprocess_streams():
    """
    Tests preprocess_streams to ensure proper cleaning and formatting of data.
    """
    mock_data = {
        "latlng": [[46.142836, 8.469562], [46.142853, 8.469612], [46.142875, 8.469717], [46.142875, 8.469759], [46.142875, 8.469759]],
        "velocity_smooth": [0.0, 0.0, 2.3, 2.2, 2.5],
        "grade_smooth": [2.6, np.nan, 1.6, np.nan, 0.6],
        "cadence": [55, np.nan, np.nan, 82, 82],
        #"heartrate": [80, 80, 84, 88, 91],
        "altitude": [904.6, 904.7, np.nan, 904.9, np.nan],
        "distance": [1.0, 4.7, 22.6, 35.8, 59.5],
        "time": [0, 1, 5, 6, 7]
    }
    mock_df = pd.DataFrame(mock_data)
    df_processed = preprocess_streams(mock_df, 5727925996)
    
    assert df_processed is not None, "Preprocessing should not return None"
    required_columns = ["distance", "altitude", "latlng", "cadence", "grade", "speed", "time", "ascent_so_far", "descent_so_far"]
    for col in required_columns:
        assert col in df_processed.columns, f"Missing required column: {col}"
    print("Processed DataFrame by preprocess_streams")
    print(df_processed.head())

def test_create_segments():
    """
    Tests create_segments function by checking segment outputs.
    """
    mock_df = pd.DataFrame({
        "time": [0,1,2,3,4],
        "distance": [0, 10, 25, 50, 100],
        "altitude": [862,899,1001,1100,1105],
        "grade": [0.1, 5.8, 7.1, 10.0, 0.3],
        "cadence": [70, 75, 65, 80, 60],
        "latlng": [[46.1, 8.4], [46.2, 8.5], [46.3, 8.6], [46.4, 8.7], [46.5, 8.8]],
        "heartrate": [110, 113, 120, 120, 125],
        "ascent_so_far": [0, 0, 1, 3, 4],
        "descent_so_far": [0, 1, 1, 1, 4]
    })
    config = {
        "gradient_tolerance": 0.5,
        "min_segment_length": 50.0,
        "max_segment_length": 200.0,
        "classification_tolerance": 2.5,
        "cadence_threshold": 60,
        "cadence_tolerance": 5,
        "rolling_window_size": 0
    }
    
    segments_df = create_segments(mock_df, 5727925996, config)
    assert not segments_df.empty, "Segmentation should return some segments"
    assert "segment_length" in segments_df.columns, "Missing 'segment_length' column"
    print("Segments created:")
    print(segments_df.head())
   
def test_segment_planned_activity(sample_planned_compressed_stream):
    """
    Tests segment_planned_activity on a minimal planned stream with only latlng and altitude.
    """
    activity_id = -67890
    duration = 3600
    segments_df = segment_planned_activity(activity_id, sample_planned_compressed_stream, duration)

    assert isinstance(segments_df, pd.DataFrame), "Output should be a pandas DataFrame"
    assert not segments_df.empty, "Segmentation should produce at least one segment"

    expected_columns = {
        "activity_id", "start_distance", "end_distance", "segment_length", 
        "avg_gradient", "avg_cadence", "movement_type", "type", "grade_category",
        "start_lat", "start_lng", "end_lat", "end_lng", "start_altitude", "end_altitude",
        "start_time", "end_time", "start_heartrate", "end_heartrate", "avg_heartrate",
        "cumulative_ascent", "cumulative_descent"
    }

    assert expected_columns.issubset(set(segments_df.columns)), \
        f"Missing expected columns: {expected_columns - set(segments_df.columns)}"

    logger.info(f"Segments created by segment_planned_activity:\n{segments_df.head()}")
    logger.info(f"GRADIENTS:\n{segments_df[["avg_gradient"]].describe()}")

def compress_stream(data):
    raw = json.dumps(data).encode("utf-8")
    return base64.b64encode(gzip.compress(raw)).decode("utf-8")

def test_parse_planned_activity_gradient():
    # Costruisci una traccia semplice con lat/lon distanti 1 km e 500 m (approssimato)
    latlng = [
        [46.0, 8.0],         # 0 m
        [46.009, 8.0],       # ~1 km nord
        [46.0135, 8.0],      # ~500 m nord
        [46.0135, 8.0]       # fermo
    ]
    altitude = [
        100.0,  # punto iniziale
        200.0,  # +100 m => ~10% su 1 km
        150.0,  # -50 m => ~-10% su 500 m
        150.0   # piano
    ]

    stream_data = [
        {"type": "latlng", "data": latlng},
        {"type": "altitude", "data": altitude}
    ]

    compressed = compress_stream(stream_data)
    compressed_stream = base64.b64decode(compressed)
    df = parse_planned_activity(compressed_stream, activity_id=123)
    logger.info(f"PARSED SEGMENTS\n{df}")
    # Verifica lunghezza
    assert len(df) == 4

    # Verifica gradienti approssimati
    assert pytest.approx(df["grade"].iloc[1], 0.5) == 10.0
    assert pytest.approx(df["grade"].iloc[2], 0.5) == -10.0
    assert pytest.approx(df["grade"].iloc[3], 0.1) == 0.0

    # Verifica distanza cumulata
    d1 = haversine(latlng[0], latlng[1], unit=Unit.METERS)
    d2 = haversine(latlng[1], latlng[2], unit=Unit.METERS)
    d3 = 0.0
    assert pytest.approx(df["distance"].iloc[1], 1) == d1
    assert pytest.approx(df["distance"].iloc[2], 1) == d1 + d2
    assert pytest.approx(df["distance"].iloc[3], 1) == d1 + d2 + d3