import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime, timezone
from app.kafka_consumer import process_message, process_retry_message

@pytest.fixture
def sample_retry_message():
    # Set retry timestamp 10 seconds after current time
    current_timestamp = int(time.time())
    retry_timestamp = current_timestamp + 10

    message = {
    "activityId": 2463829980,
    "requestParams": {
        "lat": 46.128185,
        "lon": 8.290736,
        "dt": 1560960228,
        "units": "metric"
    },
    "segmentIds": [
        "2463829980-1",
        "2463829980-2",
    ],
    "groupId": "1_8",
    "retryTimestamp": retry_timestamp
    }

    kafka_message = MagicMock()
    kafka_message.value = message  
    kafka_message.key = "2463829980"
    return kafka_message

@pytest.fixture
def sample_retry_message_expired():
    # Set retry timestamp 10 seconds before current time
    current_timestamp = int(time.time())
    retry_timestamp = current_timestamp - 10

    message = {
    "activityId": 2463829980,
    "requestParams": {
        "lat": 46.128185,
        "lon": 8.290736,
        "dt": 1560960228,
        "units": "metric"
    },
    "segmentIds": [
        "2463829980-1",
        "2463829980-2",
    ],
    "groupId": "1_8",
    "retryTimestamp": retry_timestamp
    }

    kafka_message = MagicMock()
    kafka_message.value = message  
    kafka_message.key = "2463829980"
    return kafka_message

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

@pytest.mark.parametrize('load_test_message', ['mock_segments_message.json'], indirect=True)
def test_process_message(load_test_message):
    """Tests process_message with a real Kafka message. It produces real output"""

    # Mock a success response (status 200) of the API, with the OpenWeather example structure
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
    "lat": 47.1,
    "lon": 8.6,
    "timezone": "Europe/Zurich",
    "timezone_offset": 3600,
    "data": [
        {
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
            "weather": [
                {
                    "id": 500,
                    "main": "Rain",
                    "description": "light rain",
                    "icon": "10n"
                }
            ],
            "rain": {
                "1h": 0.34
            }
        }
    ]
}

    with patch('app.weather_service.send_weather_output') as mock_send_output, \
         patch('app.weather_service.fetch_weather_data') as mock_fetch_weather_data, \
         patch('app.kafka_producer.KafkaProducer') as MockKafkaProducer, \
         patch('app.kafka_consumer.KafkaConsumer') as MockKafkaConsumer:
            mock_kafka_producer_instance = MagicMock()
            MockKafkaProducer.return_value = mock_kafka_producer_instance
            
            # Now patch the methods on the producer instance
            mock_kafka_producer_instance.send.return_value = MagicMock()
        
            # Mock fetch_weather_data response
            mock_fetch_weather_data.return_value = mock_response

            process_message(load_test_message)
            # Assertions
            assert mock_send_output.call_count == 6
            assert mock_fetch_weather_data.call_count == 6


def test_retry_message_not_processing(sample_retry_message):
    """Test that the retry message is not processed, but rescheduled."""
    print("\nTest retry message not processing")
    with patch('app.weather_service.send_weather_output'), \
        patch('app.weather_service.fetch_weather_data'):

        assert process_retry_message(sample_retry_message) == False


def test_retry_message_processing(sample_retry_message_expired):
    """Test that the retry message is processed correctly."""
    print("\nTest retry message processing")
    with patch('app.weather_service.send_weather_output'), \
        patch('app.weather_service.fetch_weather_data'):

        assert process_retry_message(sample_retry_message_expired) == True
