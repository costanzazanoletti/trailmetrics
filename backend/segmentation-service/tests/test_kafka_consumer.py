import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch
from app.kafka_consumer import process_message
from app.kafka_producer import send_segmentation_output
from app.segmentation_service import segment_activity

@pytest.fixture
def load_test_message():
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,"test_message.json")
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")

    return mock_message

def test_process_message(load_test_message):
    """Tests process_message with a real Kafka message."""

    with patch("app.kafka_consumer.send_segmentation_output") as mock_send, \
     patch("app.segmentation_service.segment_activity") as mock_segment:
        
        mock_segment.return_value = pd.DataFrame({
            "activity_id": [load_test_message.key.decode("utf-8")],  
            "start_distance": [0],
            "end_distance": [50],
            "segment_length": [50],
            "avg_gradient": [1.2],
            "avg_cadence": [80],
            "type": ["uphill"],
            "grade_category": ["2.5"],
            "start_lat": [46.132985],
            "start_lng": [8.438897],
            "end_lat": [46.132069],
            "end_lng": [8.438819]
        })

        
        process_message(load_test_message)
        mock_send.assert_called_once()
