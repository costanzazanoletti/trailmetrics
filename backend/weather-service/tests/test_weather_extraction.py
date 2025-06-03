import pytest
import pandas as pd
from app.exceptions import WeatherAPIException
from app.weather.weather_extraction import (
    compute_aggregated_wind,
    select_temp_from_summary,
    infer_weather_conditions_from_pressure,
    extract_weather_data_history,
    extract_weather_data_hourly,
    extract_weather_data_daily,
    extract_weather_data_summary
)

def test_compute_aggregated_wind():
    assert compute_aggregated_wind(4, 8) == 5.2
    assert compute_aggregated_wind(5, None) == 5.0
    assert compute_aggregated_wind(None, 6) == 6.0
    assert compute_aggregated_wind(None, None) is None

def test_select_temp_from_summary():
    temp_block = {"morning": 10, "afternoon": 15, "evening": 12, "night": 8}
    assert select_temp_from_summary(temp_block, "2024-06-01T06:00Z") == 10
    assert select_temp_from_summary(temp_block, "2024-06-01T13:00Z") == 15
    assert select_temp_from_summary(temp_block, "2024-06-01T18:00Z") == 12
    assert select_temp_from_summary(temp_block, "2024-06-01T22:00Z") == 8

def test_infer_weather_conditions_from_pressure():
    assert infer_weather_conditions_from_pressure(1025) == (800, "Clear", "clear sky")
    assert infer_weather_conditions_from_pressure(1015) == (801, "Clouds", "few clouds")
    assert infer_weather_conditions_from_pressure(1005) == (803, "Clouds", "broken clouds")
    assert infer_weather_conditions_from_pressure(995) == (500, "Rain", "light rain")
    assert infer_weather_conditions_from_pressure(None) == (None, None, None)

def test_extract_weather_data_history():
    json_data = {
        "lat": 45.0,
        "lon": 8.0,
        "data": [{
            "dt": 1700000000,
            "temp": 20,
            "feels_like": 19,
            "humidity": 80,
            "wind_speed": 2,
            "wind_gust": 6,
            "weather": [{"id": 800, "main": "Clear", "description": "clear sky"}]
        }]
    }
    result = extract_weather_data_history(json_data)
    assert result["wind"] == 3.2
    assert result["weather_id"] == 800

def test_extract_weather_data_hourly():
    ref_ts = pd.to_datetime("2024-06-01T12:30:00Z").timestamp()
    json_data = {
        "lat": 45.0,
        "lon": 8.0,
        "hourly": [
            {"dt": pd.to_datetime("2024-06-01T12:00:00Z").timestamp(), "temp": 21, "feels_like": 20, "humidity": 70, "wind_speed": 3, "wind_gust": 5, "weather": [{"id": 801, "main": "Clouds", "description": "few clouds"}]},
            {"dt": pd.to_datetime("2024-06-01T13:00:00Z").timestamp(), "temp": 22, "feels_like": 21, "humidity": 65, "wind_speed": 4, "wind_gust": 6, "weather": [{"id": 802, "main": "Clouds", "description": "scattered clouds"}]}
        ]
    }
    result = extract_weather_data_hourly(json_data, ref_ts)
    assert result["temp"] == 21
    assert result["weather_main"] == "Clouds"

def test_extract_weather_data_daily():
    ref_ts = pd.to_datetime("2024-06-01T00:00:00Z").timestamp()
    json_data = {
        "lat": 45.0,
        "lon": 8.0,
        "daily": [
            {"dt": pd.to_datetime("2024-06-01T00:00:00Z").timestamp(), "temp": {"day": 25}, "feels_like": {"day": 24}, "humidity": 60, "wind_speed": 4, "wind_gust": 6, "weather": [{"id": 500, "main": "Rain", "description": "light rain"}]}
        ]
    }
    result = extract_weather_data_daily(json_data, ref_ts)
    assert result["temp"] == 25
    assert result["weather_id"] == 500

def test_extract_weather_data_summary():
    ref_ts = pd.to_datetime("2024-06-01T15:00:00Z").timestamp()
    json_data = {
        "lat": 45.0,
        "lon": 8.0,
        "date": "2024-06-01",
        "temperature": {
            "min": 9.27,
            "max": 21.14,
            "afternoon": 18.9,
            "night": 12.25,
            "evening": 16.29,
            "morning": 13.73
            },
        "humidity": {"afternoon": 55},
        "pressure": {"afternoon": 1012},
        "wind": {"max": {"speed": 4}}
    }
    result = extract_weather_data_summary(json_data, ref_ts)
    assert result["temp"] == 18.9
    assert result["weather_main"] == "Clouds"
    assert result["wind"] == 4.0
