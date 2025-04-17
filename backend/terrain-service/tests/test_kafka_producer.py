import pytest
import json
import gzip
import base64
import pandas as pd
from app.kafka_producer import prepare_terrain_message 

def test_prepare_terrain_message(sample_segments_df):
    """Test if the message is generated with compressed segments."""
    activity_id = 123456
    user_id = "999"
    processed_at = 1741769162.4793878

    message = prepare_terrain_message(activity_id, user_id, sample_segments_df, processed_at)

    # Check the required fields
    assert "activityId" in message
    assert "userId" in message
    assert "processedAt" in message
    assert "compressedTerrainInfo" in message

    # Decode and decompress to check validity
    compressed_segments = base64.b64decode(message["compressedTerrainInfo"])
    decompressed_json = gzip.decompress(compressed_segments).decode("utf-8")
    
    # Check the processed data
    segments = json.loads(decompressed_json)
    print(segments)
    assert isinstance(segments, list), "Segments should be a list."
    assert len(segments) == len(sample_segments_df), "The number of segments should match the original data size."
