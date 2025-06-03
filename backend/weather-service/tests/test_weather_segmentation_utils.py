import pytest
import pandas as pd
import json
import gzip
from datetime import datetime, timezone
from app.weather.segment_utils import (
    parse_kafka_segments,
    decompress_segments,
    add_datetime_columns,
    create_reference_points
)

@pytest.fixture
def compressed_segments():
    segments = [
        {
            "segment_id": 1,
            "start_time": 0,
            "end_time": 60,
            "start_lat": 46.0,
            "start_lng": 8.0,
            "end_lat": 46.0005,
            "end_lng": 8.0005,
            "start_altitude": 500,
            "end_altitude": 510
        },
        {
            "segment_id": 2,
            "start_time": 70,
            "end_time": 130,
            "start_lat": 46.0005,
            "start_lng": 8.0005,
            "end_lat": 46.001,
            "end_lng": 8.001,
            "start_altitude": 510,
            "end_altitude": 600
        }
    ]
    json_bytes = json.dumps(segments).encode("utf-8")
    return gzip.compress(json_bytes)


def test_decompress_segments(compressed_segments):
    result = decompress_segments(compressed_segments)
    assert isinstance(result, list)
    assert result[0]["segment_id"] == 1


def test_parse_kafka_segments(compressed_segments):
    df = parse_kafka_segments(compressed_segments)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "segment_id" in df.columns


def test_add_datetime_columns():
    df = pd.DataFrame({
        "segment_id": [1],
        "start_time": [0],
        "end_time": [60]
    })
    ts = datetime(2024, 3, 30, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    df = add_datetime_columns(df, ts)
    assert "start_date_time" in df.columns
    assert df.loc[0, "start_date_time"].isoformat().startswith("2024-03-30T12:00")


def test_create_reference_points():
    df = pd.DataFrame({
        "segment_id": [1, 2],
        "start_time": [0, 70],
        "end_time": [60, 130],
        "start_lat": [46.0, 46.0005],
        "start_lng": [8.0, 8.0005],
        "end_lat": [46.0005, 46.001],
        "end_lng": [8.0005, 8.001],
        "start_altitude": [500, 510],
        "end_altitude": [510, 600],
        "start_date_time": [datetime(2024, 3, 30, 12, 0, 0, tzinfo=timezone.utc), datetime(2024, 3, 30, 12, 1, 10, tzinfo=timezone.utc)],
        "end_date_time": [datetime(2024, 3, 30, 12, 1, 0, tzinfo=timezone.utc), datetime(2024, 3, 30, 12, 2, 10, tzinfo=timezone.utc)]
    })
    result = create_reference_points(df, elevation_threshold=50, time_threshold=60, grid_size=0.001)
    assert isinstance(result, pd.DataFrame)
    assert "lat" in result.columns
    assert len(result) >= 1
