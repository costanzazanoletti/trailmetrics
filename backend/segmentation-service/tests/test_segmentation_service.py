import pytest
import pandas as pd
import numpy as np
import json
import gzip
from app.segmentation_service import preprocess_streams, create_segments, segment_activity, parse_kafka_stream

@pytest.fixture
def sample_compressed_stream():
    """
    Creates a sample compressed JSON stream similar to the data received from Kafka.
    """
    sample_stream = [
        {"type": "time", "data": [0, 1, 5, 9, 20]},
        {"type": "distance", "data": [0.0, 10.3, 20.4, 35.9, 55.5]},
        {"type": "altitude", "data": [300, 310, 320, 330, 340]},
        {"type": "cadence", "data": [80, 82, 83, 85, 88]},
        {"type": "latlng", "data": [[46.142836, 8.469562], [46.142853, 8.469612], [46.142875, 8.469717], 
                                        [46.142875, 8.469759], [46.142875, 8.469759]]},
        {"type": "velocity_smooth", "data": [0.0, 0.0, 0.7, 0.97, 1.21]},
        {"type": "grade_smooth", "data": [2.4, 10.0, 10.6, 0.8, 0.4]}
    ]
    
    json_data = json.dumps(sample_stream)
    compressed_data = gzip.compress(json_data.encode("utf-8"))
    
    return compressed_data

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
    expected_columns = {"activity_id", "start_distance", "end_distance", "segment_length", 
                        "avg_gradient", "avg_cadence", "movement_type", "type"}
    assert expected_columns.issubset(set(segments_df.columns)), f"Missing expected columns: {expected_columns - set(segments_df.columns)}"
    
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
        "heartrate": [80, 80, 84, 88, 91],
        "altitude": [904.6, 904.7, np.nan, 904.9, np.nan],
        "distance": [1.0, 4.7, 22.6, 35.8, 59.5],
        "time": [0, 1, 5, 6, 7]
    }
    mock_df = pd.DataFrame(mock_data)
    df_processed = preprocess_streams(mock_df, 5727925996)
    
    assert df_processed is not None, "Preprocessing should not return None"
    required_columns = ["distance", "altitude", "latlng", "cadence", "grade", "speed", "time"]
    for col in required_columns:
        assert col in df_processed.columns, f"Missing required column: {col}"
    print("Processed DataFrame by preprocess_streams")
    print(df_processed.head())

def test_create_segments():
    """
    Tests create_segments function by checking segment outputs.
    """
    mock_df = pd.DataFrame({
        "distance": [0, 10, 25, 50, 100],
        "grade": [0.1, 5.8, 7.1, 10.0, 0.3],
        "cadence": [70, 75, 65, 80, 60],
        "latlng": [[46.1, 8.4], [46.2, 8.5], [46.3, 8.6], [46.4, 8.7], [46.5, 8.8]]
    })
    config = {
        "gradient_tolerance": 0.5,
        "min_segment_length": 5.0,
        "max_segment_length": 200.0,
        "classification_tolerance": 2.5,
        "cadence_threshold": 60,
        "cadence_tolerance": 5,
        "rolling_window_size": 1
    }
    
    segments_df = create_segments(mock_df, 5727925996, config)
    assert not segments_df.empty, "Segmentation should return some segments"
    assert "segment_length" in segments_df.columns, "Missing 'segment_length' column"
    print("Segments created:")
    print(segments_df.head())
   
