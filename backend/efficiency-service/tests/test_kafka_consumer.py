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

@pytest.fixture
def load_test_message(request):
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, request.param)
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")
    return mock_message

# SEGMENTS
@patch('app.kafka_consumer.engine')
@patch('app.kafka_consumer.should_compute_similarity_for_user')
@patch('app.kafka_consumer.process_segments')
@pytest.mark.parametrize('load_test_message', ['mock_segmentation.json'], indirect=True)
def test_segments_message(mock_process_segments, mock_should_compute, mock_engine, load_test_message):
    process_segments_message(load_test_message)
    mock_process_segments.assert_called_once()
    mock_should_compute.assert_called_once_with(mock_engine, "999")

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
