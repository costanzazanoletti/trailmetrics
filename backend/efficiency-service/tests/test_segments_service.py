import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch
import base64
from datetime import datetime, timezone
from app.segments_service import process_segments
from app.exceptions import DatabaseException


@pytest.fixture
def load_sample_segments():
    """Loads a real segments from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,'mock_segmentation.json')
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")
    data = mock_message.value if isinstance(mock_message.value, dict) else json.loads(mock_message.value)
    activity_id = data.get("activityId")
    compressed_segments = data.get("compressedSegments")
    if isinstance(compressed_segments, str):
        compressed_segments = base64.b64decode(compressed_segments)
    return activity_id, compressed_segments

def test_process_segments(load_sample_segments):
    """
    Tests process_segments_message with a real Kafka message. 
    Stores data into the test Database
    """
    # Load sample data
    activity_id, compressed_segments = load_sample_segments
    
    # Call process_segments
    process_segments(activity_id, compressed_segments)

def test_process_segments_with_database_exception(load_sample_segments):
    """Tests process_segments_message with a real Kafka message."""
    with patch('app.segments_service.segments_batch_insert_and_update_status') as mock_store_segments:
        # Load sample data
        activity_id, compressed_segments = load_sample_segments
        
        # Configure mock to raise a DatabaseException
        mock_store_segments.side_effect = DatabaseException("Database error occurred while inserting segments.")

        process_segments(activity_id, compressed_segments)
        