import pytest
import json
import base64
import gzip
import pandas as pd
import os
from pathlib import Path
from app.terrain_service import get_terrain_info
import logging
import logging_setup


@pytest.fixture
def test_kafka_message():
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,"test_message.json")
    with open(file_path, "r") as file:
        data = json.load(file)
    

    # Decode like Kafka Consumer
    compressed_segments = base64.b64decode(data["value"]["compressedSegments"])
    
    return data["value"]["activityId"], compressed_segments  

def test_get_terrain_info(test_kafka_message):
    """Test that get_terrain_info returns a not empty DataFrame."""
    activity_id, compressed_segments = test_kafka_message
          
    df = get_terrain_info(activity_id, compressed_segments)

    assert isinstance(df, pd.DataFrame), "The result should be a DataFrame."
    assert not df.empty, "The DataFrame should not be empty"
