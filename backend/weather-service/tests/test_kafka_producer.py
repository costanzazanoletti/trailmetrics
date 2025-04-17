import pytest
import pandas as pd
import json
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import logging.config
from app.kafka_producer import prepare_message, send_retry_message

logging.config.fileConfig("./logging.conf")

def test_prepare_message(sample_df):
    """Test prepared_message with controlled parameters"""
    # Define input parameters
    activity_id = 12345
    reference_point_id = "1_4"
    # Call the function
    result = prepare_message(activity_id, sample_df, reference_point_id)

    # Verify the structure of the returned dictionary
    assert "activityId" in result
    assert result["activityId"] == activity_id
    assert "compressedWeatherInfo" in result
    assert "groupId" in result

    # Ensure that the "compressedWeatherInfo" field is a base64 encoded string
    assert isinstance(result["compressedWeatherInfo"], str)
    assert len(result["compressedWeatherInfo"]) > 0

    # Ensure that the compression and encoding worked by checking the type of the encoded string
    assert result["compressedWeatherInfo"].startswith("H4sIA")
    assert result["groupId"] == reference_point_id

def test_send_retry_message():
    """Test send_retry_message with controlled parameters"""
    KAFKA_RETRY_MAX_POLL_INTERVAL_MS = os.getenv("KAFKA_RETRY_MAX_POLL_INTERVAL_MS")    
    KAFKA_TOPIC_RETRY = os.getenv("KAFKA_RETRY_TOPIC_INPUT")
    
    # Test data
    activity_id = 12345
    segment_ids = ["1234-1", "1234-2"]
    request_params = {"lat": 47.1, "lon": 8.6, "appid": "fake_api_key"}
    group_id = "1_4"
    retries = 2

    # Mock the producer
    with patch('app.kafka_producer.producer.send') as mock_producer_send, \
        patch('app.kafka_producer.producer.flush') as mock_producer_flush:
    
        # Call the function you want to test
        send_retry_message(activity_id, segment_ids, group_id, request_params, retries)

        # Compute expected retry timestamp
        retry_time_seconds = (int(KAFKA_RETRY_MAX_POLL_INTERVAL_MS) / 1000) - 1
        retry_time = datetime.now(timezone.utc) + timedelta(seconds=retry_time_seconds)
        retry_timestamp = int(retry_time.timestamp())

        # Prepare the expected retry message
        expected_retry_message = {
            "activityId": activity_id,
            "requestParams": request_params,
            "segmentIds": segment_ids,
            "groupId": group_id,
            "retryTimestamp": retry_timestamp,
            "retries": retries + 1
        }

        # Check that producer.send was called with the correct parameters
        mock_producer_send.assert_called_once_with(
            KAFKA_TOPIC_RETRY,  
            key=activity_id,  
            value=expected_retry_message 
        )
        # Check that producer.flush is called once
        mock_producer_flush.assert_called_once()
