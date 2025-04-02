import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch
import base64
from datetime import datetime, timezone
from app.terrain_service import process_terrain_info
from app.exceptions import DatabaseException
from database import get_db_connection, delete_all_data

@pytest.fixture 
def set_up(autouse=True):
    print("Clear all data from database")
    delete_all_data()

@pytest.fixture
def load_sample_segments():
    """Loads a real segments from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,'mock_terrain.json')
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")
    data = mock_message.value if isinstance(mock_message.value, dict) else json.loads(mock_message.value)
    activity_id = data.get("activityId")
    compressed_terrain_info = data.get("compressedTerrainInfo")

    return activity_id, compressed_terrain_info

def test_process_terrain_info(load_sample_segments, set_up):
    """
    Tests process_terrain_info with a real Kafka message. 
    Stores data into the test Database.
    """
    # Load sample data
    activity_id, compressed_terrain_info = load_sample_segments
     
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check the number of segments before execution of process_terrain_info
    cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
    initial_count = cursor.fetchone()[0]
    
    # Call process_terrain_info
    process_terrain_info(activity_id, compressed_terrain_info)
    
    # Check the number of segments after execution of process_terrain_info
    cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
    final_count = cursor.fetchone()[0]
    
    # Check that activity_status_tracker has been updated
    cursor.execute("SELECT terrain_status FROM activity_status_tracker WHERE activity_id = %s", (activity_id,))
    terrain_status = cursor.fetchone()[0]
    
    # Assertion
    expected_rows = 193
    assert (final_count - initial_count) == expected_rows, "No segments were inserted into the database"
    assert terrain_status == True
    
    cursor.close()
    conn.close()

def test_process_terrain_info_with_database_exception(load_sample_segments,set_up):
    """Tests that process_terrain_info doesn't store any data when it handles a DatabaseException."""
    with patch('app.terrain_service.terrain_batch_insert_and_update_status') as mock_store_segments:
        # Load sample data
        activity_id, compressed_terrain_info = load_sample_segments
        
        # Configure mock to raise a DatabaseException
        mock_store_segments.side_effect = DatabaseException("Database error occurred while inserting terrain info.")
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check the number of segments before execution of process_terrain_info
        cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
        initial_count = cursor.fetchone()[0]
        
        # Call process_terrain_info
        process_terrain_info(activity_id, compressed_terrain_info)
        
        # Check the number of segments after execution of process_terrain_info
        cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
        final_count = cursor.fetchone()[0]
        
        # Assertion
        assert final_count == initial_count, "Segments with terrain info were inserted into the database"
        
        cursor.close()
        conn.close()