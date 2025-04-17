import pytest
import pandas as pd
import random
import requests
import logging.config
from unittest.mock import patch, MagicMock
from app.openweather_api_service import generate_request_parameters, fetch_weather_data, json_to_dataframe
from app.exceptions import WeatherAPIException

logging.config.fileConfig("./logging.conf")

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

def test_json_to_dataframe():
    # Mock a success response (status 200) of the API, with the OpenWeather example structure
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"lat":45.8844,"lon":8.2886,"timezone":"Europe/Rome","timezone_offset":7200,"data":[{"dt":1743397200,"sunrise":1743397716,"sunset":1743443585,"temp":-0.03,"feels_like":-3.97,"pressure":1014,"humidity":64,"dew_point":-5.34,"uvi":0,"clouds":0,"visibility":10000,"wind_speed":3.52,"wind_deg":328,"wind_gust":4.52,"weather":[{"id":800,"main":"Clear","description":"clear sky","icon":"01n"}]}]}
    
    result = json_to_dataframe(mock_response.json())

    # Verify data are as expected
    expected_length = 1
    expected_dt = 1743397200  
    expected_lat = 45.8844
    expected_lon = 8.2886
    expected_temp = -0.03
    expected_wind =  3.82 # 3.52*0.7 + 4.52*0.3
    expected_weather_description = "clear sky"
       
    assert len(result) == expected_length
    assert result.iloc[0]["lat"] == expected_lat
    assert result.iloc[0]["lon"] == expected_lon
    assert result.iloc[0]["dt"] == expected_dt
    assert result.iloc[0]["temp"] == expected_temp
    assert result.iloc[0]["wind"] == expected_wind
    assert result.iloc[0]["weather_description"] == expected_weather_description
 
def test_fetch_weather_data_success(create_sample_params):
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
         patch('app.openweather_api_service.time.sleep', return_value=None), \
         patch('app.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
        
        # Call fetch_weather_data
        result = fetch_weather_data(create_sample_params)

        # Verify that the function requests.get is called once
        requests.get.assert_called_once()

        # Verify data are as expected
        expected_length = 1
        expected_dt = 1709510400  
        expected_lat = 47.1
        expected_lon = 8.6
        expected_temp = 276.24
        expected_wind =  1.26
        expected_weather_description = "light rain"
       
        assert len(result) == expected_length
        assert result.iloc[0]["lat"] == expected_lat
        assert result.iloc[0]["lon"] == expected_lon
        assert result.iloc[0]["dt"] == expected_dt
        assert result.iloc[0]["temp"] == expected_temp
        assert result.iloc[0]["wind"] == expected_wind
        assert result.iloc[0]["weather_description"] == expected_weather_description
 
def test_fetch_weather_data_request_counter_limit(create_sample_params):
    # Mock a failure response from the request_counter.increment method
    mock_request_counter = MagicMock()
    mock_request_counter.increment.side_effect = Exception("Daily request limit reached")

    # Mock the rest of the function calls
    with patch('app.openweather_api_service.RequestCounter', return_value=mock_request_counter), \
         patch('app.openweather_api_service.time.sleep', return_value=None):
        
        # Call fetch_weather_data
        try:
            fetch_weather_data(create_sample_params)
        except WeatherAPIException as e:
            # Verify that the exception has the expected parameters
            assert str(e) == "Daily request limit reached"
            assert e.status_code == 429

def test_fetch_weather_data_429(create_sample_params):
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
         patch('app.openweather_api_service.time.sleep', return_value=None), \
         patch('app.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
      
        # Call fetch_weather_data
        try:
            fetch_weather_data(create_sample_params)
        except WeatherAPIException as e:
            # Verify that the exception has the expected parameters
            assert str(e) == "Hourly request limit reached"
            assert e.status_code == 429

        # Verify that the function requests.get is called once
        requests.get.assert_called_once()

def test_fetch_weather_data_error(create_sample_params):
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
         patch('app.openweather_api_service.time.sleep', return_value=None), \
         patch('app.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
   
        # Call fetch_weather_data
        try:
            fetch_weather_data(create_sample_params)
        except WeatherAPIException as e:
            # Verify that the exception has the expected parameters
            assert e.status_code == 400

        # Verify that the function requests.get is called once
        requests.get.assert_called_once()

def test_fetch_weather_data_generic_error(create_sample_params):
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
    mock_response.raise_for_status.side_effect = requests.exceptions.ConnectTimeout("Connection timed out")

    # Mock of the function requests.get to return mock_response
    with patch('app.openweather_api_service.requests.get', return_value=mock_response), \
         patch('app.openweather_api_service.time.sleep', return_value=None), \
         patch('app.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
   
        # Call fetch_weather_data
        try:
            fetch_weather_data(create_sample_params)
        except  WeatherAPIException as e:
            assert str(e) == "Request failed: Connection timed out"
            assert e.status_code is None