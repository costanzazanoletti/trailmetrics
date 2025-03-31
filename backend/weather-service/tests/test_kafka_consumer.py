import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch
import time
from datetime import datetime, timezone
from app.kafka_consumer import process_message, process_retry_message


@pytest.fixture
def load_test_message(request):
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,request.param)
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")

    return mock_message

# @pytest.mark.parametrize('load_test_message', ['mock_segments_message.json'], indirect=True)
# def test_process_message(load_test_message):
#     """Tests process_message with a real Kafka message. It produces real output"""
#     with patch('app.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
#         process_message(load_test_message)

# @pytest.mark.parametrize('load_test_message', ['mock_retry_message.json'], indirect=True)
# def test_process_retry_message(load_test_message):
#     """Tests process_retry_message with a real Kafka message. It produces real output"""
    
#     # Mock the current time to simulate a specific timestamp
#     # Let's say we mock the current time to be 10 seconds before retry_timestamp
#     mock_current_time = 1743416199  # 10 seconds before retry_timestamp (1743416209)

    
#     with patch('time.sleep') as mock_sleep:  # Mocking time.sleep to avoid actual waiting
#         with patch('app.kafka_consumer.datetime') as mock_datetime:  # Mocking datetime
#             # Mock datetime.now() to return a specific UTC timestamp when called
#             mock_datetime.now.return_value = datetime.fromtimestamp(mock_current_time, tz=timezone.utc)

#             with patch('app.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:    
#                 # Run the function with the mocked time
#                 process_retry_message(load_test_message)

        