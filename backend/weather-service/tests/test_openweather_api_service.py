import pytest
import pandas as pd
import random
import requests
import logging.config
from unittest.mock import patch, MagicMock
from app.openweather_api_service import generate_request_parameters, fetch_weather_data

logging.config.fileConfig("./logging.conf")

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
    return 

def test_generate_request_parameters(create_sample_dataframe):
    reference_point = create_sample_dataframe.iloc[0]
    # Call the function
    with patch.dict('os.environ', {'OPENWEATHER_API_KEY': 'mock_api_key'}):

        result = generate_request_parameters(reference_point)

        # Expected values based on the timestamp
        expected_timestamp = 1633595280 
        expected_lat = 46.000000
        expected_lon = 8.000000
        expected_units = "metric"
       
        # Assertions
        assert result["lat"] == expected_lat
        assert result["lon"] == expected_lon
        assert result["dt"] == expected_timestamp
        assert result["units"] == expected_units
  
def test_fetch_weather_data_success():
    # Mock a success response (status 200) of the API, with the OpenWeather example structure
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
    "lat": 47.1,
    "lon": 8.6,
    "timezone": "Europe/Zurich",
    "timezone_offset": 3600,
    "data": [
        {
            "dt": 1709510400,
            "sunrise": 1709531980,
            "sunset": 1709572509,
            "temp": 276.24,
            "feels_like": 276.24,
            "pressure": 1006,
            "humidity": 75,
            "dew_point": 272.35,
            "clouds": 100,
            "wind_speed": 1.26,
            "wind_deg": 262,
            "weather": [
                {
                    "id": 500,
                    "main": "Rain",
                    "description": "light rain",
                    "icon": "10n"
                }
            ],
            "rain": {
                "1h": 0.34
            }
        }
    ]
}
    # Mock of the function requests.get to return mock_response
    with patch('app.openweather_api_service.requests.get', return_value=mock_response), \
         patch('app.openweather_api_service.publish_retry_message', autospec=True) as mock_publish_retry, \
         patch('app.openweather_api_service.time.sleep', return_value=None), \
         patch('app.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
        
        activity_id = '12345'
        params = {
            "lat": 47.1,
            "lon": 8.6,
            "dt": 1709510400,
            "units": "metric",  
            "appid": 'fake_api_key'  
        }
        # Call fetch_weather_data
        result = fetch_weather_data(params, activity_id)

        # Verify that the function requests.get is called once
        requests.get.assert_called_once()

        # Ensure Kafka retry is not called (since the request was successful)
        mock_publish_retry.assert_not_called()

        # Verify data are as expected
        expected_length = 1
        expected_dt = 1709510400  
        expected_lat = 47.1
        expected_lon = 8.6
        expected_temp = 276.24
        expected_pressure = 1006
        expected_weather_description = "light rain"
       
        assert len(result) == expected_length
        assert result.iloc[0]["lat"] == expected_lat
        assert result.iloc[0]["lon"] == expected_lon
        assert result.iloc[0]["dt"] == expected_dt
        assert result.iloc[0]["temp"] == expected_temp
        assert result.iloc[0]["pressure"] == expected_pressure
        assert result.iloc[0]["weather_description"] == expected_weather_description
 
def test_fetch_weather_data_request_counter_limit():
    # Mock a failure response from the request_counter.increment method
    mock_request_counter = MagicMock()
    mock_request_counter.increment.side_effect = Exception("Daily request limit reached")


    # Mock the rest of the function calls
    with patch('app.openweather_api_service.publish_retry_message', autospec=True) as mock_publish_retry, \
         patch('app.openweather_api_service.RequestCounter', return_value=mock_request_counter), \
         patch('app.openweather_api_service.time.sleep', return_value=None):
        
        params = {
            "lat": 47.1,
            "lon": 8.6,
            "dt": 1709510400,
            "units": "metric",  
            "appid": 'fake_api_key'  
        }
        activity_id = '12345'

        # Call fetch_weather_data
        result = fetch_weather_data(params, activity_id)

        # Ensure Kafka retry is called once with a long delay
        mock_publish_retry.assert_called_once_with(params, activity_id, False)

        # Verify that the function returns None
        assert result is None

def test_fetch_weather_data_429():
    # Mock a rate limit hit response (status 429) of the API
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.json.return_value = {
        "cod":429,
        "message":"Too many requests",
        "parameters": []
    }
    # Mocking raise_for_status to raise an HTTPError when status_code is not 200
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Too many requests")
  
    # Mock of the function requests.get to return mock_response
    with patch('app.openweather_api_service.requests.get', return_value=mock_response), \
         patch('app.openweather_api_service.publish_retry_message', autospec=True) as mock_publish_retry, \
         patch('app.openweather_api_service.time.sleep', return_value=None), \
         patch('app.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
        
        activity_id = '12345'
        params = {
            "lat": 47.1,
            "lon": 8.6,
            "dt": 1709510400,
            "units": "metric",  
            "appid": 'fake_api_key'  
        }
        # Call fetch_weather_data
        result = fetch_weather_data(params, activity_id)

        # Verify that the function requests.get is called once
        requests.get.assert_called_once()

        # Ensure Kafka retry is called once with a short delay
        mock_publish_retry.assert_called_once_with(params, activity_id, True)

        # Verify that the function returns None
        assert result is None
 
def test_fetch_weather_data_error():
    # Mock a rate limit hit response (status 429) of the API
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "cod":400,
        "message":"Invalid date format",
        "parameters": [
            "date"
        ]
    }
  
    # Mocking raise_for_status to raise an HTTPError when status_code is not 200
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Bad Request")

    # Mock of the function requests.get to return mock_response
    with patch('app.openweather_api_service.requests.get', return_value=mock_response), \
         patch('app.openweather_api_service.publish_retry_message', autospec=True) as mock_publish_retry, \
         patch('app.openweather_api_service.time.sleep', return_value=None), \
         patch('app.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
        
        activity_id = '12345'
        params = {
            "lat": 47.1,
            "lon": 8.6,
            "dt": 1709510400,
            "units": "metric",  
            "appid": 'fake_api_key'  
        }
        # Call fetch_weather_data
        result = fetch_weather_data(params, activity_id)

        # Verify that the function requests.get is called once
        requests.get.assert_called_once()

        # Ensure Kafka retry is not called (since the request got an HTTP error)
        mock_publish_retry.assert_not_called()

        # Verify that the function returns None
        assert result is None
 