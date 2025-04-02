import pytest
import json
import os
import gzip
import base64
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from app.weather_service import process_weather_info
from app.exceptions import DatabaseException
from database import get_db_connection, delete_all_data


@pytest.fixture 
def set_up(autouse=True):
    print("\nTEST SET UP :Clear all data from database\n")
    delete_all_data()

@pytest.fixture
def load_sample_segments():
    """Loads a real segments from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,'mock_weather.json')
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")
    data = mock_message.value if isinstance(mock_message.value, dict) else json.loads(mock_message.value)
    activity_id = data.get("activityId")
    group_id = data.get("groupId")
    compressed_weather_info = data.get("compressedWeatherInfo")

    return activity_id, group_id, compressed_weather_info

def dataframe_to_compressed_json(df):
    # Convert the DataFrame to a list of dictionaries 
    json_data = df.to_dict(orient="records") 
    # Convert the list of dictionaries to JSON string and then compress it
    json_str = json.dumps(json_data).encode("utf-8")
    compressed_json = gzip.compress(json_str)
    # Encode the compressed data to base64
    return base64.b64encode(compressed_json).decode("utf-8")

def test_process_weather_info(load_sample_segments, set_up):
    """
    Tests process_weather_info with a real Kafka message. 
    Stores data into the test Database.
    """
    # Load sample data
    activity_id, group_id, compressed_weather_info = load_sample_segments

    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check the number of segments before execution of process_segments
    cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
    initial_count = cursor.fetchone()[0]

    # Call process_weather_info
    process_weather_info(activity_id, group_id, compressed_weather_info)
    
    # Check the number of segments after execution of process_weather_info
    cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
    final_count = cursor.fetchone()[0]
    
    # Check that weather_data_progress has  been updated
    cursor.execute("SELECT saved FROM weather_data_progress WHERE activity_id = %s AND group_id = %s", (activity_id, group_id,))
    group_saved = cursor.fetchone()[0]

    # Check that activity_status_tracker has not been updated
    cursor.execute("SELECT weather_status FROM activity_status_tracker WHERE activity_id = %s", (activity_id,))
    result = cursor.fetchone()
    weather_status = None
    if result is not None:
        weather_status = result[0]
    
    # Assertion
    expected_rows = 3
    assert (final_count - initial_count) == expected_rows, "Segments were not inserted into the database"
    assert group_saved == True
    assert not weather_status
    
    cursor.close()
    conn.close()

def test_process_weather_info_with_complete_progress(set_up):
    """
    Tests repeated invocations of process_weather_info. 
    Stores data into the test Database and updates the activity_status_tracker.
    """
    # Create sample data
    data_1 = {
        'segment_id': ["987-1","987-2"],
        'lat': [46.0807, 46.0807],
        'lon': [8.2799, 8.2799],
        'dt':[1738159835, 1738159835],
        'temp': [9.74, 9.74],
        'feels_like': [8.74, 8.74],
        'humidity':[61, 61],
        'wind':[1.03, 1.03],
        'weather_id':[803, 803],
        'weather_main':['Clouds', 'Clouds'],
        'weather_description':['broken clouds', 'broken clouds'],
    }

    data_2 = {
        'segment_id': ["987-3","987-4"],
        'lat': [46.1122, 46.1122],
        'lon': [8.2801, 8.2801],
        'dt':[1738159999, 1738159999],
        'temp': [9.91, 9.91],
        'feels_like': [9.11, 9.11],
        'humidity':[61, 61],
        'wind':[1.05, 1.05],
        'weather_id':[501, 501],
        'weather_main':['Rain', 'Rain'],
        'weather_description':['light rain', 'light rain'],
    }

    activity_id = 987
    group_id_1 = "1_2"
    compressed_weather_info_1 = dataframe_to_compressed_json(pd.DataFrame(data_1))
    group_id_2 = "2_2"
    compressed_weather_info_2 = dataframe_to_compressed_json(pd.DataFrame(data_2))

    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check the number of segments before execution of process_segments
    cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
    initial_count = cursor.fetchone()[0]

    # Call process_weather_info once per group_id
    process_weather_info(activity_id, group_id_1, compressed_weather_info_1)
    process_weather_info(activity_id, group_id_2, compressed_weather_info_2)
    
    # Check the number of segments after execution of process_weather_info
    cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
    final_count = cursor.fetchone()[0]
    
    # Check that weather_data_progress has  been updated
    cursor.execute("SELECT saved FROM weather_data_progress WHERE activity_id = %s AND group_id = %s", (activity_id, group_id_1,))
    group_saved_1 = cursor.fetchone()[0]
    cursor.execute("SELECT saved FROM weather_data_progress WHERE activity_id = %s AND group_id = %s", (activity_id, group_id_2,))
    group_saved_2 = cursor.fetchone()[0]

    # Check that activity_status_tracker has not been updated
    cursor.execute("SELECT weather_status FROM activity_status_tracker WHERE activity_id = %s", (activity_id,))
    result = cursor.fetchone()
    weather_status = None
    if result is not None:
        weather_status = result[0]
    
    # Assertion
    expected_rows = 4
    assert (final_count - initial_count) == expected_rows, "Segments were not inserted into the database"
    assert group_saved_1 == True
    assert group_saved_2 == True
    assert weather_status == True
    
    cursor.close()
    conn.close()

def test_process_weather_info_with_database_exception(load_sample_segments,set_up):
    """Tests that process_weather_info doesn't store any data when it handles a DatabaseException."""
    with patch('app.weather_service.weather_batch_insert_and_update_status') as mock_store_segments:
        # Load sample data
        activity_id, group_id, compressed_weather_info = load_sample_segments
        
        # Configure mock to raise a DatabaseException
        mock_store_segments.side_effect = DatabaseException("Database error occurred while inserting weather info.")
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check the number of segments before execution of process_weather_info
        cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
        initial_count = cursor.fetchone()[0]
        
        # Call process_weather_info
        process_weather_info(activity_id, group_id, compressed_weather_info)
        
        # Check the number of segments after execution of process_weather_info
        cursor.execute("SELECT COUNT(*) FROM segments WHERE activity_id = %s", (activity_id,))
        final_count = cursor.fetchone()[0]
        
        # Assertion
        assert final_count == initial_count, "Segments with weather info were inserted into the database"
        
        cursor.close()
        conn.close()