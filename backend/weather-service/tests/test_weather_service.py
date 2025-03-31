import pytest
import pandas as pd
import logging.config
from unittest.mock import patch
from app.weather_service import create_reference_points, assign_weather_to_segments, get_weather_info
from app.exceptions import WeatherAPIException

logging.config.fileConfig("./logging.conf")

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

def test_create_reference_points(sample_df_segments):
 
    elevation_threshold = 50  
    time_threshold = 600       
    
    # Run the function to get the reference points
    result_df = create_reference_points(sample_df_segments, elevation_threshold, time_threshold)
    
    # Print the result for debugging
    print(f"Reference points:\n{result_df.head()}")
    
    # Check the number of points selected
    assert len(result_df) == 5
    
    # Check the first point
    assert result_df.iloc[0]["lat"] == 46.0
    assert result_df.iloc[0]["lng"] == 8.0
    
def test_assign_weather_to_segments(sample_reference_point, sample_df_weather_response):
    # Get the segment ids
    segment_ids = sample_reference_point["associated_segments"]
    # Call the function
    result_df = assign_weather_to_segments(segment_ids, sample_df_weather_response)
    
    print(f"Result assign weather to segments\n{result_df.head()}")
    
    # Verify that only associated segments are present
    assert len(result_df) == 3  
    assert set(result_df["segment_id"].values) == set(sample_reference_point["associated_segments"])
    
    # Verify that weather info are correctly added
    assert "temp" in result_df.columns
    assert "feels_like" in result_df.columns
    assert "wind" in result_df.columns
    assert "humidity" in result_df.columns
    assert "weather_description" in result_df.columns
    
    # Verifica that the weather data are correct
    assert result_df["temp"].iloc[0] == 273.1
    assert result_df["feels_like"].iloc[0] == 272.5
    assert result_df["wind"].iloc[0] == 5.2
    assert result_df["humidity"].iloc[0] == 80
    assert result_df["weather_description"].iloc[0] == "light rain"

    # Verifica that a segment not associated is not present
    assert "123456-5" not in result_df["segment_id"].values

def test_get_weather_info_success(sample_df_segments, sample_df_weather_response):
    # Define input parameters for the function
    activity_start_date = 1627315508.0
    compressed_segments = b"compressed_segments"  # Simulated compressed segments
    activity_id = 12345
    processed_at = 1743092455.4382648

    with patch('app.weather_service.parse_kafka_segments', return_value=sample_df_segments), \
         patch('app.weather_service.add_datetime_columns', return_value=sample_df_segments), \
         patch('app.weather_service.fetch_weather_data', return_value=sample_df_weather_response) as mock_fetch_weather_data, \
         patch('app.weather_service.send_weather_output') as mock_send_output, \
         patch('app.weather_service.send_retry_message') as mock_send_retry:
        
        # Call the function
        get_weather_info(activity_start_date, compressed_segments, activity_id)

         # Verify that fetch_weather_data was called once for each reference point
        assert mock_fetch_weather_data.call_count == 2 

        # Verify that send_weather_output was called once for each successful fetch
        assert mock_send_output.call_count == 2 

        # Verify that send_retry_message was not called (since there were no exceptions)
        mock_send_retry.assert_not_called()

def test_get_weather_info_failure(sample_df_segments):
    # Define input parameters for the function
    activity_start_date = 1627315508.0
    compressed_segments = b"compressed_segments"  # Simulated compressed segments
    activity_id = 12345
    processed_at = 1743092455.4382648

    with patch('app.weather_service.parse_kafka_segments', return_value=sample_df_segments), \
         patch('app.weather_service.add_datetime_columns', return_value=sample_df_segments), \
         patch('app.weather_service.fetch_weather_data', side_effect= WeatherAPIException("Request failed")) as mock_fetch_weather_data, \
         patch('app.weather_service.send_weather_output') as mock_send_output, \
         patch('app.weather_service.send_retry_message') as mock_send_retry:
        
        # Call the function
        get_weather_info(activity_start_date, compressed_segments, activity_id)

         # Verify that fetch_weather_data was called once for each reference point
        assert mock_fetch_weather_data.call_count == 2 

        # Verify that send_weather_output was never called because each fetch failed
        mock_send_output.assert_not_called()

        # Verify that send_retry_message was not called (since there were no rate limit exceptions)
        mock_send_retry.assert_not_called()

def test_get_weather_info_429(sample_df_segments):
    # Define input parameters for the function
    activity_start_date = 1627315508.0
    compressed_segments = b"compressed_segments"  # Simulated compressed segments
    activity_id = 12345
    processed_at = 1743092455.4382648

    with patch('app.weather_service.parse_kafka_segments', return_value=sample_df_segments), \
         patch('app.weather_service.add_datetime_columns', return_value=sample_df_segments), \
         patch('app.weather_service.fetch_weather_data', side_effect= WeatherAPIException("Hourly request limit reached", status_code=429, retry_in_hour=True)) as mock_fetch_weather_data, \
         patch('app.weather_service.send_weather_output') as mock_send_output, \
         patch('app.weather_service.send_retry_message') as mock_send_retry:
        
        # Call the function
        get_weather_info(activity_start_date, compressed_segments, activity_id)

         # Verify that fetch_weather_data was called once for each reference point
        assert mock_fetch_weather_data.call_count == 2 

        # Verify that send_weather_output was never called because each fetch failed
        mock_send_output.assert_not_called()

        # Verify that send_retry_message was called once for each rate limit hit
        assert mock_send_retry.call_count == 2
