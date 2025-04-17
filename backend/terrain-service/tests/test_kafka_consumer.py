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

    
    process_message(load_test_message)
    mock_send.assert_called_once()
