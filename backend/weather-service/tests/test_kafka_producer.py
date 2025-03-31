import pytest
import pandas as pd
from datetime import datetime, timezone
from unittest.mock import patch
import logging.config
from app.kafka_producer import prepare_message, prepare_retry_message

logging.config.fileConfig("./logging.conf")

@pytest.fixture
def sample_df():
    sample_data =  {
        'segment_id': ["1234-1", "1234-2"],
        'lat': [47.11, 47.11],
        'lon': [8.68, 8.68],
        'dt': [1709510400, 1709510400],
        'temp': [273.1, 273.1],
        'feels_like': [272.5, 272.5],
        'humidity': [80, 80],
        'wind': [5.2, 5.2],
        'weather_id': [500, 500],
        'weather_main': ['Rain', 'Rain'],
        'weather_description': ['light rain', 'light rain']
    }
    return pd.DataFrame(sample_data)

# Test prepare_message function
def test_prepare_message(sample_df):
    # Define input parameters
    activity_id = 12345

    # Call the function
    result = prepare_message(activity_id, sample_df)

    # Verify the structure of the returned dictionary
    assert "activityId" in result
    assert result["activityId"] == activity_id
    assert "compressedWeatherInfo" in result

    # Ensure that the "compressedWeatherInfo" field is a base64 encoded string
    assert isinstance(result["compressedWeatherInfo"], str)
    assert len(result["compressedWeatherInfo"]) > 0

    # Ensure that the compression and encoding worked by checking the type of the encoded string
    assert result["compressedWeatherInfo"].startswith("H4sIA")

def test_prepare_retry_message_short():
    activity_id = 12345
    segment_ids = ["1234-1", "1234-2"]
    request_params = {"lat": 47.1, "lon": 8.6, "appid": "fake_api_key"}
    short = True

    # Call the function
    result = prepare_retry_message(activity_id, segment_ids, request_params, short)

    # Verify the structure of the returned dictionary
    assert "activityId" in result
    assert result["activityId"] == activity_id
    assert "requestParams" in result
    assert result["requestParams"] == request_params
    assert "segmentIds" in result
    assert result["segmentIds"] == segment_ids  
    assert "retryTimestamp" in result

    # Verify retry_timestamp is in the future (1 hour added)
    retry_time = datetime.fromtimestamp(result["retryTimestamp"], tz=timezone.utc)
    assert retry_time > datetime.now(timezone.utc)

def test_prepare_retry_message_long():
    activity_id = 12345
    segment_ids = ["1234-1", "1234-2"]
    request_params = {"lat": 47.1, "lon": 8.6, "appid": "fake_api_key"}
    short = False

    # Call the function
    result = prepare_retry_message(activity_id, segment_ids, request_params, short)

    # Verify the structure of the returned dictionary
    assert "activityId" in result
    assert result["activityId"] == activity_id
    assert "requestParams" in result
    assert result["requestParams"] == request_params
    assert "segmentIds" in result
    assert result["segmentIds"] == segment_ids  
    assert "retryTimestamp" in result
    # Verify retry_timestamp is at the start of the next day (00:00 UTC)
    retry_time = datetime.fromtimestamp(result["retryTimestamp"], tz=timezone.utc)
    assert retry_time.hour == 0
    assert retry_time.minute == 0
    assert retry_time.second == 0
    assert retry_time > datetime.now(timezone.utc)