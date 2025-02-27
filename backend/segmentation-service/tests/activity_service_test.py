import pytest
from app.services.activity_service import get_activity_streams

# Replace with a valid activity_id from your database
TEST_ACTIVITY_ID = 5727925996  

def test_get_activity_streams():
    df = get_activity_streams(TEST_ACTIVITY_ID)
    
    assert not df.empty, "DataFrame should not be empty"
    assert "latlng" in df.columns, "Missing 'latlng' column"
    assert "velocity_smooth" in df.columns, "Missing 'velocity_smooth' column"
    
    print("Extracted Activity Streams:")
    print(df.head())  # Show the first few rows

