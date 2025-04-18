import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime, timezone
from app.kafka_consumer import process_message, process_retry_message

@patch('app.kafka_consumer.get_weather_info')
@pytest.mark.parametrize('load_test_message', ['mock_segments_message.json'], indirect=True)
def test_process_message(mock_get_weather_info, load_test_message):
    """Tests process_message with a real Kafka message. It produces real output"""
    
    # Call the function
    process_message(load_test_message)

    #Assertions
    mock_get_weather_info.assert_called_once()

@patch('app.kafka_consumer.get_weather_info')
def test_not_process_message(mock_get_weather_info):
    """Tests process_message with a mock Kafka message that is not processable."""
    
    payload = {
        "activityId": 123,
        "userId": "999",
        "startDate": 1627917322.0,
        "processedAt": 1743418280.9846733,
        "status": "failure",
        "compressedSegments":""
    }

    # Simulate KafkaProducer serialization
    key = str(123).encode("utf-8")
    value = json.dumps(payload).encode("utf-8")

    # Mock Kafka message
    mock_message = Mock()
    mock_message.key = key
    mock_message.value = value

    # Call the function
    process_message(mock_message)

    # Assertions
    mock_get_weather_info.assert_not_called()

@patch('app.kafka_consumer.get_weather_data_from_api')
@patch('time.sleep')
def test_retry_message_processing_with_delay(mock_sleep, mock_get_weather_data):
    """Test that the retry message is processed with the delay."""
    # Mock data
    current_timestamp = int(time.time())
    retry_timestamp = current_timestamp + 10
    activity_id = 2463829980
    request_params = {
        "lat": 46.128185,
        "lon": 8.290736,
        "dt": 1560960228,
        "units": "metric"
    }
    segment_ids = ["2463829980-1", "2463829980-2"]
    group_id = "1_8"
    retries = 3

    message = {
        "activityId": activity_id,
        "requestParams": request_params,
        "segmentIds": segment_ids,
        "groupId": group_id,
        "retryTimestamp": retry_timestamp,
        "retries": retries
    }

    kafka_message = MagicMock()
    kafka_message.value = message
    kafka_message.key = "2463829980"

    # Call the function
    process_retry_message(kafka_message)

    # Assertions
    mock_sleep.assert_called_once_with(retry_timestamp - int(datetime.now(timezone.utc).timestamp()))
    mock_get_weather_data.assert_called_once_with(activity_id, segment_ids, request_params, group_id, retries)

@patch('app.kafka_consumer.get_weather_data_from_api')
@patch('time.sleep')
def test_retry_message_processing_immediately(mock_sleep, mock_get_weather_data):
    """Test that the retry message is processed immediately."""
    
    # Mock the data
    current_timestamp = int(time.time())
    retry_timestamp = current_timestamp - 10
    activity_id = 2463829980
    request_params = {
        "lat": 46.128185,
        "lon": 8.290736,
        "dt": 1560960228,
        "units": "metric"
    }
    segment_ids = ["2463829980-1", "2463829980-2"]
    group_id = "1_8"
    retries = 3

    message = {
        "activityId": activity_id,
        "requestParams": request_params,
        "segmentIds": segment_ids,
        "groupId": group_id,
        "retryTimestamp": retry_timestamp,
        "retries": retries
    }

    kafka_message = MagicMock()
    kafka_message.value = message
    kafka_message.key = "2463829980"

    # Call the function
    process_retry_message(kafka_message)

    # Assertions
    mock_sleep.assert_not_called()
    mock_get_weather_data.assert_called_once_with(activity_id, segment_ids, request_params, group_id, retries)
