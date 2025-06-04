import pytest
import json
import os
import gzip
import pandas as pd
from unittest.mock import Mock

@pytest.fixture
def load_test_message():
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,"mock_message_debug.json")
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")

    return mock_message

@pytest.fixture
def load_planned_test_message():
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,"mock_planned_message.json")
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")

    return mock_message

@pytest.fixture
def sample_segments_df():
    """Create a test DataFrame"""
    data = {
        "start_distance": [0.0, 50.0],
        "end_distance": [50.0, 100.0],
        "segment_length": [50.0, 50.0],
        "avg_gradient": [-5.0, 2.0],
        "avg_cadence": [80, 85],
        "type": ["downhill", "uphill"],
        "grade_category": [-5, 2],
        "start_lat": [46.1, 46.2],
        "start_lng": [8.4, 8.5],
        "end_lat": [46.15, 46.25],
        "end_lng": [8.45, 8.55],
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_compressed_stream():
    """
    Creates a sample compressed JSON stream similar to the data received from Kafka.
    """
    sample_stream = [
        {"type": "time", "data": [0, 1, 5, 9, 20]},
        {"type": "distance", "data": [0.0, 20.3, 50.4, 135.9, 255.5]},
        {"type": "altitude", "data": [300, 310, 320, 330, 340]},
        {"type": "cadence", "data": [80, 82, 83, 85, 88]},
        {"type": "latlng", "data": [[46.142836, 8.469562], [46.142853, 8.469612], [46.142875, 8.469717], 
                                        [46.142875, 8.469759], [46.142875, 8.469759]]},
        {"type": "velocity_smooth", "data": [0.0, 0.0, 0.7, 0.97, 1.21]},
        {"type": "grade_smooth", "data": [10.0, 10.0, 10.6, 0.8, 0.4]},
        {"type": "heartrate", "data":[115, 117, 125, 130, 130]}
    ]
    
    json_data = json.dumps(sample_stream)
    compressed_data = gzip.compress(json_data.encode("utf-8"))
    
    return compressed_data
    
@pytest.fixture
def sample_planned_compressed_stream():
    """
    Creates a sample compressed JSON stream for planned activity (altitude + latlng only),
    with distances and elevation changes large enough to trigger segmentation.
    """
    sample_stream = [
        {"type": "altitude", "data": [100, 150, 100, 130, 90]},  # forti salite/discese
        {"type": "latlng", "data": [
            [46.142800, 8.469500],
            [46.143800, 8.470500],  # ~140m
            [46.144800, 8.471500],  # ~140m
            [46.145800, 8.472500],  # ~140m
            [46.146800, 8.473500]   # ~140m
        ]}
    ]
    
    json_data = json.dumps(sample_stream)
    compressed_data = gzip.compress(json_data.encode("utf-8"))
    
    return compressed_data

