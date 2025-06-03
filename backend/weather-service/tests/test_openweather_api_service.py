import pytest
import pandas as pd
import random
import requests
from datetime import datetime
import logging.config
from unittest.mock import patch, MagicMock
from app.api.openweather_api_service import generate_request_parameters, fetch_weather_data
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

def test_fetch_history_weather_data_success(create_sample_params):
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
    with patch('app.api.openweather_api_service.requests.get', return_value=mock_response), \
         patch('app.api.openweather_api_service.time.sleep', return_value=None), \
         patch('app.api.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
        
        # Call fetch_weather_data
        result = fetch_weather_data(create_sample_params)

        # Verify that the function requests.get is called once
        requests.get.assert_called_once()
        data = result['data'][0]
        assert data.get("temp") == 276.24
 
def test_fetch_weather_data_request_counter_limit(create_sample_params):
    # Mock a failure response from the request_counter.increment method
    mock_request_counter = MagicMock()
    mock_request_counter.increment.side_effect = Exception("Daily request limit reached")

    # Mock the rest of the function calls
    with patch('app.api.openweather_api_service.RequestCounter', return_value=mock_request_counter), \
         patch('app.api.openweather_api_service.time.sleep', return_value=None):
        
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
    with patch('app.api.openweather_api_service.requests.get', return_value=mock_response), \
         patch('app.api.openweather_api_service.time.sleep', return_value=None), \
         patch('app.api.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
      
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
    with patch('app.api.openweather_api_service.requests.get', return_value=mock_response), \
         patch('app.api.openweather_api_service.time.sleep', return_value=None), \
         patch('app.api.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
   
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
    with patch('app.api.openweather_api_service.requests.get', return_value=mock_response), \
         patch('app.api.openweather_api_service.time.sleep', return_value=None), \
         patch('app.api.counter_manager.RequestCounter.increment', autospec=True) as mock_increment:
   
        # Call fetch_weather_data
        try:
            fetch_weather_data(create_sample_params)
        except  WeatherAPIException as e:
            assert str(e) == "Request failed: Connection timed out"
            assert e.status_code is None

@pytest.fixture
def reference_point():
    return {
        "lat": 46.0,
        "lng": 8.0,
        "timestamp": datetime(2024, 3, 30, 15, 8, 0)
    }

@pytest.mark.parametrize("api_type, expected_key", [
    ("hourly", "hourly"),
    ("daily", "daily"),
    ("summary", "temperature")
])
def test_fetch_weather_data_success_for_each_api(reference_point, api_type, expected_key):
    mock_json = {
        "lat": reference_point["lat"],
        "lon": reference_point["lng"]
    }

    if api_type == "summary":
        mock_json.update({
            "date": "2024-03-30",
            "temperature": {
                "morning": 275,
                "afternoon": 280,
                "evening": 278,
                "night": 273
            },
            "humidity": {"afternoon": 80},
            "pressure": {"afternoon": 1021},
            "wind": {"max": {"speed": 4.2}}
        })
    else:
        mock_json[expected_key] = [
            {
                "dt": 1709510400,
                "temp": 280,
                "humidity": 80,
                "wind_speed": 2.5,
                "wind_gust": 3.5,
                "weather": [{
                    "id": 800,
                    "main": "Clear",
                    "description": "clear sky"
                }]
            }
        ]

    with patch("app.api.openweather_api_service.requests.get") as mock_get, \
         patch("app.api.openweather_api_service.time.sleep", return_value=None), \
         patch("app.api.counter_manager.RequestCounter.increment", autospec=True):

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_json
        mock_get.return_value = mock_response

        params = generate_request_parameters(reference_point, api_type=api_type)
        result = fetch_weather_data(params, api_type=api_type)

        assert result["lat"] == reference_point["lat"]
        assert result["lon"] == reference_point["lng"]
