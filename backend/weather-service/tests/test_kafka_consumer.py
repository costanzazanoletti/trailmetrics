import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch
from app.kafka_consumer import process_message
from app.kafka_producer import send_weather_output


@pytest.fixture
def load_test_message():
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,"mock_segments_message.json")
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")

    return mock_message

def test_process_message(load_test_message):
    """Tests process_message with a real Kafka message."""

    with patch("app.kafka_consumer.send_weather_output") as mock_send:

        process_message(load_test_message)
        mock_send.assert_called_once()
