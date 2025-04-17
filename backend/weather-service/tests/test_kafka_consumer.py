import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
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

@patch('app.kafka_consumer.get_weather_info')
@pytest.mark.parametrize('load_test_message', ['mock_segments_message.json'], indirect=True)
def test_process_message(mock_get_weather_info, load_test_message):
    """Tests process_message with a real Kafka message. It produces real output"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "lat": 47.1,
        "lon": 8.6,
        "timezone": "Europe/Zurich",
        "timezone_offset": 3600,
        "data": [{
            "dt": 1709510400,
            "sunrise": 1709531980,
            "sunset": 1709572509,
            "temp": 276.24,
            "feels_like": 276.24,
            "pressure": 1006,
            "humidity": 75,
            "dew_point": 272.35,
            "clouds": 100,
            "wind_speed": 1.26,
            "wind_deg": 262,
            "weather": [{"id": 500, "main": "Rain", "description": "light rain", "icon": "10n"}],
            "rain": {"1h": 0.34}
        }]
    }

    process_message(load_test_message)
    mock_get_weather_info.assert_called_once()


@patch('app.kafka_consumer.get_weather_data_from_api')
@patch('time.sleep')
def test_retry_message_processing_with_delay(mock_sleep, mock_get_weather_data):
    """Test that the retry message is processed with the delay."""
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

    process_retry_message(kafka_message)

    mock_sleep.assert_called_once_with(retry_timestamp - int(datetime.now(timezone.utc).timestamp()))
    mock_get_weather_data.assert_called_once_with(activity_id, segment_ids, request_params, group_id, retries)

@patch('app.kafka_consumer.get_weather_data_from_api')
@patch('time.sleep')
def test_retry_message_processing_immediately(mock_sleep, mock_get_weather_data):
    """Test that the retry message is processed immediately."""
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

    process_retry_message(kafka_message)

    mock_sleep.assert_not_called()
    mock_get_weather_data.assert_called_once_with(activity_id, segment_ids, request_params, group_id, retries)
