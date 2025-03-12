import pytest
import json
import gzip
import base64
import pandas as pd
from app.kafka_producer import prepare_segmentation_message  

@pytest.fixture
def sample_segments_df():
    """Create a test DataFrame"""
    data = {
        "start_distance": [0.0, 50.0],
        "end_distance": [50.0, 100.0],
        "segment_length": [50.0, 50.0],
        "avg_gradient": [-5.0, 2.0],
        "avg_cadence": [80, 85],
        "type": ["downhill", "uphill"],
        "grade_category": [-5, 2],
        "start_lat": [46.1, 46.2],
        "start_lng": [8.4, 8.5],
        "end_lat": [46.15, 46.25],
        "end_lng": [8.45, 8.55],
    }
    return pd.DataFrame(data)

def test_prepare_segmentation_message(sample_segments_df):
    """Test if the message is generated with compressed segments."""
    activity_id = 123456
    processed_at = 1741769162.4793878

    message = prepare_segmentation_message(activity_id, sample_segments_df, processed_at)

    # Check the required fields
    assert "activityId" in message
    assert "processedAt" in message
    assert "compressedSegments" in message

    # Decode and decompress to check validity
    compressed_segments = base64.b64decode(message["compressedSegments"])
    decompressed_json = gzip.decompress(compressed_segments).decode("utf-8")
    
    # Check the processed data
    segments = json.loads(decompressed_json)
    print(segments)
    assert isinstance(segments, list), "Segments should be a list."
    assert len(segments) == len(sample_segments_df), "The number of segments should match the original data size."
