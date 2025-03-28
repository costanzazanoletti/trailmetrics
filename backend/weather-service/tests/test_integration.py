import pytest
import pandas as pd
import os
import json
import base64
import logging.config
from unittest.mock import patch
from app.weather_service import get_weather_info
from app.exceptions import WeatherAPIException

logging.config.fileConfig("./logging.conf")

@pytest.fixture
def sample_kafka_message():
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,"mock_segments_message.json")
    with open(file_path, "r") as file:
        data = json.load(file)

    start_date = data["value"]["startDate"]
    activity_id = data["value"]["activityId"]
    processed_at = data["value"]["processedAt"]

    # Decode like Kafka Consumer
    compressed_segments = base64.b64decode(data["value"]["compressedSegments"])
    return start_date, compressed_segments, activity_id, processed_at  


def test_get_weather_info(sample_kafka_message):
    """Integration test to verify the behavior of get_weather_info with real data."""
    start_date, compressed_segments, activity_id, processed_at = sample_kafka_message
    with patch('app.counter_manager.RequestCounter.increment', autospec=True), \
         patch('app.weather_service.send_weather_output') as mock_send:
        get_weather_info(start_date, compressed_segments, activity_id, processed_at)
    
    # Verify that the Kafka output message is sent
    assert mock_send.call_count == 6

def test_get_weather_info_retry(sample_kafka_message):
    """Integration test to verify the behavior of get_weather_info with real data."""
    start_date, compressed_segments, activity_id, processed_at = sample_kafka_message
    with patch('app.counter_manager.RequestCounter.increment', autospec=True), \
         patch('app.weather_service.send_retry_message') as mock_send_retry, \
         patch('app.weather_service.fetch_weather_data', side_effect= WeatherAPIException("Hourly request limit reached", status_code=429, retry_in_hour=True)) as mock_fetch_weather_data:
         
        get_weather_info(start_date, compressed_segments, activity_id, processed_at)
    
    # Verify that the API request is sent
    assert mock_fetch_weather_data.call_count == 6
    # Verify that the retry message is sent
    assert mock_send_retry.call_count == 6