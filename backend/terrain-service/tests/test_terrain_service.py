import pytest
import json
import base64
import gzip
import pandas as pd
import os
from pathlib import Path
from app.terrain_service import get_terrain_info, create_bounding_boxes
import logging
import logging_setup


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

def test_get_terrain_info(test_kafka_message):
    """Test that get_terrain_info returns a not empty DataFrame."""
    activity_id, compressed_segments = test_kafka_message
          
    df = get_terrain_info(activity_id, compressed_segments)
    print(df.head())

    assert isinstance(df, pd.DataFrame), "The result should be a DataFrame."
    assert not df.empty, "The DataFrame should not be empty"

def test_create_bounding_boxes():
    # Test per un'attività con un'area grande
    min_lat, max_lat = 46.0, 46.5
    min_lng, max_lng = 8.0, 8.5

    bounding_boxes = create_bounding_boxes(min_lat, max_lat, min_lng, max_lng, lat_step=0.1, lng_step=0.1)
    assert len(bounding_boxes) == 25, "The number of bounding boxes should be 25."

