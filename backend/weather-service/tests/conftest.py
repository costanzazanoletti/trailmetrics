import pytest
import json
import os
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture
def load_test_message(request):
    """Loads a real Kafka message from a JSON file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir,request.param)
    with open(file_path, "r") as file:
        message_data = json.load(file)
    
    mock_message = Mock()
    mock_message.key = message_data["key"].encode("utf-8")
    mock_message.value = json.dumps(message_data["value"]).encode("utf-8")

    return mock_message

@pytest.fixture
def sample_df():
    sample_data =  {
        'segment_id': ["1234-1", "1234-2"],
        'lat': [47.11, 47.11],
        'lon': [8.68, 8.68],
        'dt': [1709510400, 1709510400],
        'temp': [273.1, 273.1],
        'feels_like': [272.5, 272.5],
        'humidity': [80, 80],
        'wind': [5.2, 5.2],
        'weather_id': [500, 500],
        'weather_main': ['Rain', 'Rain'],
        'weather_description': ['light rain', 'light rain']
    }
    return pd.DataFrame(sample_data)

@pytest.fixture
def create_sample_dataframe():
    # Create a sample DataFrame
    data = {
        'lat': [46.000000, 46.109305, 46.106291, 46.106291],
        'lng': [8.000000, 8.287756, 8.287467, 8.287467],
        'distance': [0, 1000, 2000, 2000],
        'altitude':[100,200, 300, 300],
        'timestamp': ['2021-10-07 08:28:00', '2021-10-07 08:32:41', '2021-10-07 08:40:09', '2021-10-07 08:40:09'],
        'distance:traveled': [0,1000,1000,0],
        'time_elapsed':[0.0, 281.0, 448.0, 0.0],
        'elevation_change':[0,100,100,0]
    }
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    return pd.DataFrame(data)

@pytest.fixture
def create_sample_params():
    return {
            "lat": 47.1,
            "lon": 8.6,
            "dt": 1709510400,
            "units": "metric",  
            "appid": 'fake_api_key'  
        }

@pytest.fixture
def sample_df_segments():
    # Sample data for the test with added variation
    data = {
        "activity_id": [123456, 123456, 123456, 123456, 123456, 123456, 123456, 123456, 123456, 123456, 
                        123456, 123456, 123456, 123456, 123456, 123456, 123456, 123456, 123456, 123456],
        "segment_id": ["123456-1", "123456-2", "123456-3", "123456-4", "123456-5", "123456-6", "123456-7", 
                       "123456-8", "123456-9", "123456-10", "123456-11", "123456-12", "123456-13", 
                       "123456-14", "123456-15", "123456-16", "123456-17", "123456-18", "123456-19", "123456-20"],
        "start_lat": [46.0, 46.1, 46.2, 46.3, 46.4, 46.5, 46.6, 46.7, 46.8, 46.9, 
                      47.0, 47.1, 47.2, 47.3, 47.4, 47.5, 47.6, 47.7, 47.8, 47.9],
        "start_lng": [8.0, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 
                      9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9],
        "start_distance": [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 
                           1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
        "end_distance": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 
                         1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000],
        "start_altitude": [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 
                           200, 210, 220, 230, 240, 250, 260, 270, 280, 290],
        "end_altitude": [110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 
                         210, 220, 230, 240, 250, 260, 270, 280, 290, 300],
        "start_date_time": [
            "2021-10-07 08:28:00", "2021-10-07 08:28:56", "2021-10-07 08:29:13", "2021-10-07 08:29:44", 
            "2021-10-07 08:30:04", "2021-10-07 08:30:24", "2021-10-07 08:31:01", "2021-10-07 08:31:20", 
            "2021-10-07 08:31:55", "2021-10-07 08:32:12", "2021-10-07 08:32:47", "2021-10-07 08:33:38", 
            "2021-10-07 08:34:37", "2021-10-07 08:35:19", "2021-10-07 08:35:54", "2021-10-07 08:36:36", 
            "2021-10-07 08:37:25", "2021-10-07 08:38:10", "2021-10-07 08:38:51", "2021-10-07 08:39:31"
        ],
        "end_date_time": [
            "2021-10-07 08:28:54", "2021-10-07 08:29:11", "2021-10-07 08:29:37", "2021-10-07 08:30:01", 
            "2021-10-07 08:30:18", "2021-10-07 08:30:54", "2021-10-07 08:31:16", "2021-10-07 08:31:48", 
            "2021-10-07 08:32:09", "2021-10-07 08:32:41", "2021-10-07 08:33:30", "2021-10-07 08:34:31", 
            "2021-10-07 08:35:14", "2021-10-07 08:35:53", "2021-10-07 08:36:23", "2021-10-07 08:37:15", 
            "2021-10-07 08:38:09", "2021-10-07 08:38:38", "2021-10-07 08:39:25", "2021-10-07 08:40:09"
        ],
        "end_lat": [46.114561, 46.114141, 46.113507, 46.112945, 46.112534, 46.111572, 46.111116, 46.110354, 46.109787, 46.109305,
                    46.108794, 46.108699, 46.108424, 46.108054, 46.107830, 46.107491, 46.107053, 46.106770, 46.106334, 46.106291],
        "end_lng": [8.290780, 8.290502, 8.290235, 8.289816, 8.289471, 8.289002, 8.288392, 8.287771, 8.287914, 8.287756,
                    8.287484, 8.288483, 8.289024, 8.289425, 8.289067, 8.288304, 8.287764, 8.287427, 8.287072, 8.287467]   
    }
    
    # Convert dates in dateformat
    data["start_date_time"] = pd.to_datetime(data["start_date_time"])
    data["end_date_time"] = pd.to_datetime(data["end_date_time"])

    return pd.DataFrame(data)

@pytest.fixture
def sample_reference_point():
    # Mock one reference_point with associated segments
    return {
        "associated_segments": ["123456-1", "123456-2", "123456-3"]
    }

@pytest.fixture
def sample_df_weather_response():
    return pd.DataFrame({
    'lat': [47.1],
    'lon': [8.6],
    'dt': [1709510400],
    'temp': [273.1],
    'feels_like': [272.5],
    'humidity': [80],
    'wind': [5.2],
    'weather_id': [500],
    'weather_main': ['Rain'],
    'weather_description': ['light rain']
})
