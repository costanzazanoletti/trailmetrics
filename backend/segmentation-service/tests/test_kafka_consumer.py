import pytest

import pandas as pd
from unittest.mock import Mock, patch
from app.kafka_consumer import process_message
from app.kafka_producer import send_segmentation_output
from app.segmentation_service import segment_activity


@patch("app.kafka_consumer.send_segmentation_output")
def test_process_message(mock_send, load_test_message):
    """Tests process_message with a real Kafka message."""           
    process_message(load_test_message)
    mock_send.assert_called_once()
