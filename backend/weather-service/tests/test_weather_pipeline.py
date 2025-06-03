import pytest
import pandas as pd
import json
import gzip
import base64
import logging.config
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from app.weather.weather_pipeline import (
    choose_api_type, 
    get_weather_data_from_api, 
    get_weather_info)
from app.exceptions import WeatherAPIException
from datetime import datetime, timezone, timedelta

logging.config.fileConfig("./logging.conf")

def test_choose_api_type_history():
    now = datetime.now(timezone.utc)
    # past
    start_date = int((now - timedelta(days=1)).timestamp())
    duration = 3600  # 1h
    assert choose_api_type(start_date, duration) == "history"
    # future < 48h
    start_date = int((now + timedelta(hours=10)).timestamp())
    duration = 3600 
    assert choose_api_type(start_date, duration) == "hourly"
    # future > 48h and < 8d
    start_date = int((now + timedelta(days=2)).timestamp())
    duration = int(timedelta(days=2).total_seconds())
    assert choose_api_type(start_date, duration) == "daily"
    # future > 8 days 
    start_date = int((now + timedelta(days=10)).timestamp())
    duration = int(timedelta(days=2).total_seconds())
    assert choose_api_type(start_date, duration) == "summary"
    # future > 1.5y
    start_date = int(now.timestamp())
    duration = int(timedelta(days=550).total_seconds())
    with pytest.raises(ValueError, match="Planned activity exceeds forecast availability"):
        choose_api_type(start_date, duration)

# Test get_weather_data_from_api with retry on 429
def test_get_weather_data_from_api_retries_on_429():
    mock_fetch = MagicMock(side_effect=WeatherAPIException("limit", status_code=429))
    with patch("app.weather.weather_pipeline.fetch_weather_data", mock_fetch), \
         patch("app.weather.weather_pipeline.send_retry_message") as mock_retry:
        get_weather_data_from_api("hourly", "act_1", [1,2], {"dt": 123, "lat": 45, "lon": 9}, "1_1", 0)
        mock_retry.assert_called_once()

# Test get_weather_info main flow (mocked)
def test_get_weather_info_flow():
    now = datetime.now(timezone.utc)
    activity_start = int(now.timestamp())
    duration = 3600
    activity_id = "test_act"

    # Simulated single segment
    segment = {
        "segment_id": 1,
        "start_lat": 45.0,
        "start_lng": 9.0,
        "end_lat": 45.01,
        "end_lng": 9.01,
        "start_altitude": 300,
        "end_altitude": 320,
        "start_time": 0,
        "end_time": 600
    }
    raw = json.dumps([segment]).encode("utf-8")
    compressed_segments = gzip.compress(raw)

    with patch("app.weather.weather_pipeline.fetch_weather_data") as mock_fetch, \
         patch("app.weather.weather_pipeline.send_weather_output") as mock_send:
        mock_fetch.return_value = {
            "lat": 45.0,
            "lon": 9.0,
            "data": [{
                "dt": activity_start,
                "temp": 18,
                "feels_like": 18,
                "humidity": 50,
                "wind_speed": 3,
                "wind_gust": 5,
                "weather": [{"id": 800, "main": "Clear", "description": "clear sky"}]
            }]
        }
        get_weather_info(activity_start, duration, compressed_segments, activity_id)
        mock_send.assert_called_once()

# Test get_weather_info end to end with sample message
@pytest.mark.parametrize(
    "time_offset, duration, expected_api",
    [
        (timedelta(hours=1), 3600, "hourly"),
        (timedelta(days=2), 86400, "daily"),
        (timedelta(days=9), 86400, "summary"),
    ]
)
@pytest.mark.parametrize("load_test_message", ["mock_planned_message.json"], indirect=True)
def test_get_weather_info_end_to_end(load_test_message, time_offset, duration, expected_api):
    message = load_test_message
    activity_id = json.loads(message.key.decode("utf-8"))
    payload = json.loads(message.value.decode("utf-8"))
    compressed_segments = base64.b64decode(payload["compressedSegments"])
    now = datetime.now(timezone.utc)
    start_date = int((now + time_offset).timestamp())
    duration = payload["duration"]
    is_planned = payload["isPlanned"]

    with (
        patch("app.weather.weather_pipeline.send_weather_output") as mock_send,
        patch("app.weather.weather_pipeline.send_retry_message") as mock_retry
    ):
        get_weather_info(start_date, duration, compressed_segments, activity_id, is_planned=is_planned)

        mock_send.assert_called()
        mock_retry.assert_not_called()

