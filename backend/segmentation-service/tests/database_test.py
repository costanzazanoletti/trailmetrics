import pytest
from app.database import get_raw_activity_streams

TEST_ACTIVITY_ID = 5727925996

def test_get_activity_streams():
    df = get_raw_activity_streams(TEST_ACTIVITY_ID)
    
    assert not df.empty, "DataFrame should not be empty"
    assert "type" in df.columns, "Missing 'type' column"
    assert "data" in df.columns, "Missing 'data' column"

    print("Extracted Raw Activity Streams:")
    print(df.head())
