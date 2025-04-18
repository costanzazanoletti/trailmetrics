import pytest
import json
import gzip
import base64
import pandas as pd
from app.kafka_producer import prepare_segmentation_message  

def test_prepare_segmentation_message(sample_segments_df):
    """Test if the message is generated with compressed segments."""
    activity_id = 123456
    user_id = "123456"
    start_date = 1741183458.000000000
    processed_at = 1741769162.4793878
    status = 'success'

    message = prepare_segmentation_message(activity_id, user_id, sample_segments_df, processed_at, start_date, status)

    # Check the required fields
    assert "activityId" in message
    assert "startDate" in message
    assert "processedAt" in message
    assert "status" in message
    assert "compressedSegments" in message

    # Decode and decompress to check validity
    compressed_segments = base64.b64decode(message["compressedSegments"])
    decompressed_json = gzip.decompress(compressed_segments).decode("utf-8")
    
    # Check the processed data
    segments = json.loads(decompressed_json)
    print(segments)
    assert isinstance(segments, list), "Segments should be a list."
    assert len(segments) == len(sample_segments_df), "The number of segments should match the original data size."
