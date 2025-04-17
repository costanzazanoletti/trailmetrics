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
    file_path = os.path.join(base_dir,"mock_message_debug.json")
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")

    return mock_message
@patch("app.kafka_consumer.send_segmentation_output")
def test_process_message(mock_send, load_test_message):
    """Tests process_message with a real Kafka message."""           
    process_message(load_test_message)
    mock_send.assert_called_once()
