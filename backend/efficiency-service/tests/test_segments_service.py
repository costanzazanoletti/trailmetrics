import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch
import base64
from datetime import datetime, timezone
from app.segments_service import process_segments
from app.exceptions import DatabaseException
from database import get_db_connection


@pytest.fixture
def load_sample_segments():
    """Loads a real segments from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,'mock_segmentation.json')
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")
    data = mock_message.value if isinstance(mock_message.value, dict) else json.loads(mock_message.value)
    activity_id = data.get("activityId")
    compressed_segments = data.get("compressedSegments")
    if isinstance(compressed_segments, str):
        compressed_segments = base64.b64decode(compressed_segments)
    return activity_id, compressed_segments

def delete_segments_for_activity(activity_id):
    """Cancella tutti i segmenti per un dato activity_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Esegui il comando DELETE
    cursor.execute("DELETE FROM segments WHERE activity_id = %s", (activity_id,))
    cursor.execute("DELETE FROM activity_status_tracker WHERE activity_id = %s", (activity_id,))
    # Conferma le modifiche
    conn.commit()
    
    cursor.close()
    conn.close()

def test_process_segments(load_sample_segments):
    """
    Tests process_segments_message with a real Kafka message. 
    Stores data into the test Database.
    """
    # Load sample data
    activity_id, compressed_segments = load_sample_segments
    
    # Clear segments table
    delete_segments_for_activity(activity_id)
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check the number of segments before execution of process_segments
    cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
    initial_count = cursor.fetchone()[0]
    
    # Call process_segments
    process_segments(activity_id, compressed_segments)
    
    # Check the number of segments after execution of process_segments
    cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
    final_count = cursor.fetchone()[0]
    
    # Check that activity_status_tracker has been updated
    cursor.execute("SELECT segment_status FROM activity_status_tracker WHERE activity_id = %s", (activity_id,))
    segment_status = cursor.fetchone()[0]
    
    # Assertion
    expected_rows = 226
    assert (final_count - initial_count) == expected_rows, "No segments were inserted into the database"
    assert segment_status == True
    
    cursor.close()
    conn.close()

def test_process_segments_with_database_exception(load_sample_segments):
    """Tests that process_segments_message doesn't store any data when it handles a DatabaseException."""
    with patch('app.segments_service.segments_batch_insert_and_update_status') as mock_store_segments:
        # Load sample data
        activity_id, compressed_segments = load_sample_segments
        
        # Configure mock to raise a DatabaseException
        mock_store_segments.side_effect = DatabaseException("Database error occurred while inserting segments.")

        # Clear segments table
        delete_segments_for_activity(activity_id)
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check the number of segments before execution of process_segments
        cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
        initial_count = cursor.fetchone()[0]
        
        # Call process_segments
        process_segments(activity_id, compressed_segments)
        
        # Check the number of segments after execution of process_segments
        cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
        final_count = cursor.fetchone()[0]
        
        # Assertion
        assert final_count == initial_count, "Segments were inserted into the database"
        
        cursor.close()
        conn.close()

def test_process_segments_for_existing_activity(load_sample_segments):
    """
    Tests process_segments_message when the activity has already been processed.
    """
    # Load sample data
    activity_id, compressed_segments = load_sample_segments
    
    # Clear segments table
    delete_segments_for_activity(activity_id)
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check the number of segments before execution of process_segments
    cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
    initial_count = cursor.fetchone()[0]
    
    # Call process_segments
    process_segments(activity_id, compressed_segments)
    # Call process_segments a second time so that segments exist
    process_segments(activity_id, compressed_segments)
    
    # Check the number of segments after execution of process_segments
    cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
    final_count = cursor.fetchone()[0]
    
    # Assertion
    expected_rows = 226
    assert (final_count - initial_count) == expected_rows, "No segments were inserted into the database"
    
    cursor.close()
    conn.close()        