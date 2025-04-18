import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch
from app.kafka_consumer import process_message
from app.kafka_producer import send_terrain_output
from app.terrain_service import get_terrain_info

@patch("app.kafka_consumer.send_terrain_output")
@patch("app.terrain_service.get_terrain_info")
def test_process_message(mock_terrain_info, mock_send, load_test_message):
    """Tests process_message with a real Kafka message."""
    # Mock api call to get terrain info
    mock_terrain_info.return_value = pd.DataFrame({
        "segment_id": ["2767750533-1"],  
        "start_distance": [2.6],
        "end_distance": [168.1],
        "segment_length": [171.7],
        "avg_gradient": [2.11],
        "avg_cadence": [69.130435],
        "type": ["downhill"],
        "grade_category": ["2.5"],
        "start_lat": [46.115901],
        "start_lng": [8.291248],
        "end_lat": [46.114561],
        "end_lng": [8.290780 ],
        "highway": ["track"],
        "surface": ["dirt"]
    })
    
    # Call the function
    process_message(load_test_message)
    mock_send.assert_called_once()
    args, kwargs = mock_send.call_args

    #Assertions
    assert args[0] == 5727925996  # activity_id
    assert args[1] == "999"      # user_id
    assert isinstance(args[2], pd.DataFrame) and not args[2].empty  # compressedTerrainInfo

@patch("app.kafka_consumer.send_terrain_output")
def test_not_process_message(mock_send):
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
    mock_send.assert_not_called()