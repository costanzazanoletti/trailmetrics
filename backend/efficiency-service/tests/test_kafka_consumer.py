import pytest
import json
import os
from unittest.mock import Mock, patch
from app.kafka_consumer import (
    process_segments_message, 
    process_terrain_message, 
    process_weather_message, 
    process_deleted_activities_message
)
from database import engine, fetch_one_sql

# SEGMENTS
@patch('app.kafka_consumer.engine')
@patch('app.kafka_consumer.should_compute_similarity_for_user')
@patch('app.kafka_consumer.process_segments')
@pytest.mark.parametrize('load_test_message', ['mock_segmentation.json'], indirect=True)
def test_segments_message_with_success_status(mock_process_segments, mock_should_compute, mock_engine, load_test_message):
    """Test process segments message with a real Kafka message"""
    # Call the function
    process_segments_message(load_test_message)
    # Assertions
    mock_process_segments.assert_called_once()
    mock_should_compute.assert_called_once_with(mock_engine, "999")

@patch('app.kafka_consumer.engine')
@patch('app.kafka_consumer.should_compute_similarity_for_user')
@patch('app.kafka_consumer.process_segments')
@patch('app.kafka_consumer.insert_not_processable_actitivity_status')
def test_segments_message_with_failure_status(mock_insert_not_processable,mock_process_segments, mock_should_compute, mock_engine):
    """Test process segments message with a mock Kafka message with failure status"""
    # Mock segmentation output message 
    activity_id = 123
    payload = {
        "activityId": activity_id,
        "userId": "999",
        "startDate": 1627917322.0,
        "processedAt": 1743418280.9846733,
        "status": "failure",
        "compressedSegments":""
    }

    # Simulate KafkaProducer serialization
    key = str(activity_id).encode("utf-8")
    value = json.dumps(payload).encode("utf-8")

    # Mock Kafka message
    mock_message = Mock()
    mock_message.key = key
    mock_message.value = value

    # Call the function
    process_segments_message(mock_message)

    # Assertions
    mock_insert_not_processable.assert_called_once_with(activity_id, mock_engine)
    mock_process_segments.assert_not_called()
    mock_should_compute.assert_called_once_with(mock_engine, "999")

def test_segments_message_with_failure_status_and_db(set_up):
    """
        Integration test: process segments message with failure status and save to database.
    """
    # Mock segmentation output message 
    activity_id = 123
    payload = {
        "activityId": activity_id,
        "userId": "999",
        "startDate": 1627917322.0,
        "processedAt": 1743418280.9846733,
        "status": "failure",
        "compressedSegments":""
    }

    # Simulate KafkaProducer serialization
    key = str(activity_id).encode("utf-8")
    value = json.dumps(payload).encode("utf-8")

    # Mock Kafka message
    mock_message = Mock()
    mock_message.key = key
    mock_message.value = value

    # Call the function
    process_segments_message(mock_message)

    # Assertions
    with engine.begin() as connection:
        result = fetch_one_sql(connection, "SELECT not_processable FROM activity_status_tracker WHERE activity_id = :id", {"id": activity_id})
        assert result and result[0] == True

# TERRAIN
@patch('app.kafka_consumer.engine')
@patch('app.kafka_consumer.should_compute_similarity_for_user')
@patch('app.kafka_consumer.process_terrain_info')
@pytest.mark.parametrize('load_test_message', ['mock_terrain.json'], indirect=True)
def test_terrain_message(mock_process_terrain, mock_should_compute, mock_engine, load_test_message):
    process_terrain_message(load_test_message)
    mock_process_terrain.assert_called_once()
    mock_should_compute.assert_called_once_with(mock_engine, "999")

# WEATHER
@patch('app.kafka_consumer.engine')
@patch('app.kafka_consumer.get_user_id_from_activity')
@patch('app.kafka_consumer.should_compute_similarity_for_user')
@patch('app.kafka_consumer.process_weather_info')
@pytest.mark.parametrize('load_test_message', ['mock_weather.json'], indirect=True)
def test_weather_message(mock_process_weather, mock_should_compute, mock_get_user_id, mock_engine, load_test_message):
    mock_get_user_id.return_value = "42"
    process_weather_message(load_test_message)
    mock_get_user_id.assert_called_once_with(mock_engine, 123)
    mock_process_weather.assert_called_once()
    mock_should_compute.assert_called_once_with(mock_engine, "42")

# DELETED ACTIVITIES
@patch('app.kafka_consumer.engine')
@patch('app.kafka_consumer.should_compute_similarity_for_user')
@patch('app.kafka_consumer.process_deleted_activities')
@pytest.mark.parametrize('load_test_message', ['mock_deleted_activities.json'], indirect=True)
def test_deleted_activities_message(mock_process_deleted, mock_should_compute, mock_engine, load_test_message):
    process_deleted_activities_message(load_test_message)
    mock_process_deleted.assert_called_once()
    mock_should_compute.assert_called_once_with(mock_engine, "999")
