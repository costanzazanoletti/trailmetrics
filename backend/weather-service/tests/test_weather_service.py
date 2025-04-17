import pytest
import pandas as pd
import logging.config
from unittest.mock import patch
from app.weather_service import create_reference_points, assign_weather_to_segments, get_weather_info
from app.exceptions import WeatherAPIException

logging.config.fileConfig("./logging.conf")

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

    with patch('app.weather_service.parse_kafka_segments', return_value=sample_df_segments), \
         patch('app.weather_service.add_datetime_columns', return_value=sample_df_segments), \
         patch('app.weather_service.fetch_weather_data', side_effect= WeatherAPIException("Hourly request limit reached", status_code=429)) as mock_fetch_weather_data, \
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
