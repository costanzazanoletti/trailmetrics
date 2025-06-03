import pandas as pd
from app.weather.weather_assignment import assign_weather_to_segments

def test_assign_weather_to_segments():
    segment_ids = [1, 2, 3]
    weather_data = {
        "lat": [46.0],
        "lon": [8.0],
        "dt": [1709510400],
        "temp": [280],
        "feels_like": [278],
        "humidity": [80],
        "wind": [3.0],
        "weather_id": [800],
        "weather_main": ["Clear"],
        "weather_description": ["clear sky"]
    }
    weather_df = pd.DataFrame(weather_data)
    assigned_df = assign_weather_to_segments(segment_ids, weather_df)

    assert isinstance(assigned_df, pd.DataFrame)
    assert len(assigned_df) == 3
    assert set(assigned_df["segment_id"]) == set(segment_ids)
    assert all(assigned_df["temp"] == 280)
    assert all(assigned_df["weather_main"] == "Clear")
