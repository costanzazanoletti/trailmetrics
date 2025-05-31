import pytest
import pandas as pd
from unittest.mock import patch
from app.kafka_consumer import process_message
from app.kafka_producer import send_segmentation_output
from app.segmentation_service import segment_activity, segment_planned_activity


@patch("app.kafka_consumer.send_segmentation_output")
def test_process_message_success(mock_send_output, load_test_message):
    """Tests process_message with a real Kafka message."""           
    process_message(load_test_message)
    mock_send_output.assert_called_once()
    args, kwargs = mock_send_output.call_args
    assert args[0] == 6846977895  # activity_id
    assert args[1] == "6846977895"      # user_id
    assert isinstance(args[2], pd.DataFrame) and not args[2].empty  # segments_df
    assert args[5] == "success"

@patch("app.kafka_consumer.send_segmentation_output")
@patch("app.kafka_consumer.segment_activity")
def test_process_message_failure(mock_segment_activity, mock_send_output, load_test_message):
    """Tests process_message and mock missing columns.""" 
    # Mock segmentation output
    mock_segment_activity.return_value = pd.DataFrame()
    # Call the funciton
    process_message(load_test_message)

    # Assert call to send_segmentation_output
    mock_send_output.assert_called_once()
    args, kwargs = mock_send_output.call_args

    assert args[0] == 6846977895  # activity_id
    assert args[1] == "6846977895"      # user_id
    assert isinstance(args[2], pd.DataFrame) and args[2].empty  # segments_df
    assert args[5] == "failure"

@patch("app.kafka_consumer.send_segmentation_output")
def test_process_planned_message_success(mock_send_output, load_planned_test_message):
    """Tests process_message with a real Kafka message."""           
    process_message(load_planned_test_message)
    mock_send_output.assert_called_once()
    args, kwargs = mock_send_output.call_args
    assert args[0] == -1748617807957  # activity_id
    assert args[1] == "28658549"      # user_id
    assert isinstance(args[2], pd.DataFrame) and not args[2].empty  # segments_df
    assert args[5] == "success"