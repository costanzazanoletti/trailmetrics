import pytest
import json
import os
import gzip
import base64
import pandas as pd
from unittest.mock import Mock, patch

@pytest.fixture
def load_test_message():
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,"mock_message.json")
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
        "segment_id": ["2767750533-1", "2767750533-2", "2767750533-3"],
        "highway": ["residential", "residential","secondary"],
        "surface": ["sett","asphalt", None]
    }
    return pd.DataFrame(data)

@pytest.fixture
def test_kafka_message():
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,"mock_message.json")
    with open(file_path, "r") as file:
        data = json.load(file)
    

    # Decode like Kafka Consumer
    compressed_segments = base64.b64decode(data["value"]["compressedSegments"])
    
    return data["value"]["activityId"], compressed_segments  
