import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch
import time
from datetime import datetime, timezone
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
    file_path = os.path.join(base_dir,request.param)
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")

    return mock_message

@pytest.mark.parametrize('load_test_message', ['mock_segmentation.json'], indirect=True)
def test_segments_message(load_test_message):
    """Tests process_segments_message with a real Kafka message."""
    with patch('app.kafka_consumer.process_segments') as mock_process_segments, \
         patch('app.kafka_consumer.should_compute_similarity_for_user') as mock_should_compute_similarity:
        process_segments_message(load_test_message)
    # Assertions
    mock_process_segments.assert_called_once
    mock_should_compute_similarity.assert_called_once

@pytest.mark.parametrize('load_test_message', ['mock_terrain.json'], indirect=True)
def test_terrain_message(load_test_message):
    """Tests process_terrain_message with a real Kafka message."""
    with patch('app.kafka_consumer.process_terrain_info') as mock_process_terrain, \
         patch('app.kafka_consumer.should_compute_similarity_for_user') as mock_should_compute_similarity:
        process_terrain_message(load_test_message)
    # Assertions
    mock_process_terrain.assert_called_once
    mock_should_compute_similarity.assert_called_once

@pytest.mark.parametrize('load_test_message', ['mock_weather.json'], indirect=True)
def test_weather_message(load_test_message):
    """Tests process_weather_message with a real Kafka message."""
    with patch('app.kafka_consumer.process_weather_info') as mock_process_weather, \
         patch('app.kafka_consumer.should_compute_similarity_for_user') as mock_should_compute_similarity:
        process_weather_message(load_test_message)
    # Assertions
    mock_process_weather.assert_called_once
    mock_should_compute_similarity.assert_called_once

@pytest.mark.parametrize('load_test_message', ['mock_deleted_activities.json'], indirect=True)
def test_deleted_activities_message(load_test_message):
    """Tests process_deleted_activities_message with a real Kafka message."""
    with patch('app.kafka_consumer.process_deleted_activities') as mock_process_deleted, \
         patch('app.kafka_consumer.should_compute_similarity_for_user') as mock_should_compute_similarity:
        process_deleted_activities_message(load_test_message)
    # Assertions
    mock_process_deleted.assert_called_once
    mock_should_compute_similarity.assert_called_once