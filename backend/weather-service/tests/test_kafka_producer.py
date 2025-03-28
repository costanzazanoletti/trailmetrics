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
        "lat": [47.1, 47.2],
        "lon": [8.6, 8.7],
        "dt": [1709510400, 1709511000],
        "elevation": [500, 600],
        "distance": [1000, 1500]
    }
    return pd.DataFrame(sample_data)

@pytest.fixture
def sample_reference_point():
    # Sample DataFrame for reference point
    sample_reference_data = {
        "lat": [47.1],
        "lon": [8.6],
        "dt": [1709510400],
        "elevation": [500],
        "distance": [1000]
    }
    return pd.DataFrame(sample_reference_data)

# Test prepare_message function
def test_prepare_message(sample_df):
    # Define input parameters
    activity_id = 12345
    processed_at = 1743092455.4382648

    # Call the function
    result = prepare_message(activity_id, sample_df, processed_at)

    # Verify the structure of the returned dictionary
    assert "activityId" in result
    assert result["activityId"] == activity_id
    assert "processedAt" in result
    assert result["processedAt"] == processed_at
    assert "compressedWeatherInfo" in result

    # Ensure that the "compressedWeatherInfo" field is a base64 encoded string
    assert isinstance(result["compressedWeatherInfo"], str)
    assert len(result["compressedWeatherInfo"]) > 0

    # Ensure that the compression and encoding worked by checking the type of the encoded string
    assert result["compressedWeatherInfo"].startswith("H4sIA")

def test_prepare_retry_message_short(sample_reference_point):
    activity_id = 12345
    reference_point = sample_reference_point.iloc[0]
    request_params = {"lat": 47.1, "lon": 8.6, "appid": "fake_api_key"}
    short = True

    # Call the function
    result = prepare_retry_message(activity_id, reference_point, request_params, short)

    # Verify the structure of the returned dictionary
    assert "activityId" in result
    assert result["activityId"] == activity_id
    assert "request_params" in result
    assert result["request_params"] == request_params
    assert "reference_point" in result
    assert isinstance(result["reference_point"], dict)  
    assert len(result["reference_point"]) == len(reference_point)
    assert "retry_timestamp" in result

    # Verify retry_timestamp is in the future (1 hour added)
    retry_time = datetime.fromtimestamp(result["retry_timestamp"], tz=timezone.utc)
    assert retry_time > datetime.now(timezone.utc)


# Test prepare_retry_message function (short=False)
def test_prepare_retry_message_long(sample_reference_point):
    activity_id = 12345
    reference_point = sample_reference_point.iloc[0]
    request_params = {"lat": 47.1, "lon": 8.6, "appid": "fake_api_key"}
    short = False

    # Call the function
    result = prepare_retry_message(activity_id, reference_point, request_params, short)

    # Verify the structure of the returned dictionary
    assert "activityId" in result
    assert result["activityId"] == activity_id
    assert "request_params" in result
    assert result["request_params"] == request_params
    assert "reference_point" in result
    assert isinstance(result["reference_point"], dict)  
    assert len(result["reference_point"]) == len(reference_point)
    assert "retry_timestamp" in result

    # Verify retry_timestamp is at the start of the next day (00:00 UTC)
    retry_time = datetime.fromtimestamp(result["retry_timestamp"], tz=timezone.utc)
    assert retry_time.hour == 0
    assert retry_time.minute == 0
    assert retry_time.second == 0
    assert retry_time > datetime.now(timezone.utc)