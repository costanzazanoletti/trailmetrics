import pandas as pd
from app.exceptions import WeatherAPIException

def compute_aggregated_wind(wind_speed, wind_gust, alpha=0.7):
    """Returns a weighted average of wind speed and gust, or the available value."""
    
    if wind_speed is not None and wind_gust is not None:
        return round(alpha * wind_speed + (1 - alpha) * wind_gust, 2)
    elif wind_speed is not None:
        return round(wind_speed, 2)
    elif wind_gust is not None:
        return round(wind_gust, 2)
    return None

def select_temp_from_summary(temp_block, reference_timestamp):
    """Selects the most relevant temperature value based on the hour of the reference timestamp."""
    
    if isinstance(reference_timestamp, (int, float)):
        hour = pd.to_datetime(reference_timestamp, unit="s").hour
    else:
        hour = pd.to_datetime(reference_timestamp).hour
    if 5 <= hour < 12:
        return temp_block.get("morning")
    elif 12 <= hour < 17:
        return temp_block.get("afternoon")
    elif 17 <= hour < 21:
        return temp_block.get("evening")
    else:
        return temp_block.get("night")

def infer_weather_conditions_from_pressure(pressure):
    """Infers basic weather condition (id, main, description) based on pressure levels."""
    
    if pressure is None:
        return None, None, None
    if pressure >= 1020:
        return 800, "Clear", "clear sky"
    elif 1010 <= pressure < 1020:
        return 801, "Clouds", "few clouds"
    elif 1000 <= pressure < 1010:
        return 803, "Clouds", "broken clouds"
    return 500, "Rain", "light rain"

def extract_weather_data(api_type, weather_json, reference_timestamp):
    """Dispatches the appropriate extraction function depending on the API type."""

    if api_type == "history":
        return extract_weather_data_history(weather_json)
    elif api_type == "hourly":
        return extract_weather_data_hourly(weather_json, reference_timestamp)
    elif api_type == "daily":
        return extract_weather_data_daily(weather_json, reference_timestamp)
    elif api_type == "summary":
        return extract_weather_data_summary(weather_json, reference_timestamp)
    else:
        raise ValueError(f"Unsupported API type: {api_type}")

def extract_weather_data_history(weather_json):
    """Extracts and normalizes weather data from a 'history' API response."""

    if "data" not in weather_json or not weather_json["data"]:
        raise WeatherAPIException("Missing or empty 'data' in history response")
    data = weather_json["data"][0]
    weather = data.get("weather", [{}])[0]
    wind = compute_aggregated_wind(data.get("wind_speed"), data.get("wind_gust"))
    return {
        "lat": weather_json["lat"],
        "lon": weather_json["lon"],
        "dt": data.get("dt"),
        "temp": data.get("temp"),
        "feels_like": data.get("feels_like"),
        "humidity": data.get("humidity"),
        "wind": wind,
        "weather_id": weather.get("id"),
        "weather_main": weather.get("main"),
        "weather_description": weather.get("description"),
    }

def extract_weather_data_hourly(weather_json, reference_timestamp):
    """Extracts the closest hourly forecast to the reference timestamp and normalizes it."""

    if "hourly" not in weather_json:
        raise WeatherAPIException("Missing 'hourly' field in weather response")
    df = pd.DataFrame(weather_json["hourly"])
    df["dt"] = pd.to_datetime(df["dt"], unit="s", utc=True)
    target_dt = pd.to_datetime(reference_timestamp, utc=True)
    df["time_diff"] = (df["dt"] - target_dt).abs()
    closest = df.loc[df["time_diff"].idxmin()]
    weather = closest.get("weather", [{}])[0]
    wind = compute_aggregated_wind(closest.get("wind_speed"), closest.get("wind_gust"))
    return {
        "lat": weather_json["lat"],
        "lon": weather_json["lon"],
        "dt": int(closest["dt"].timestamp()),
        "temp": closest.get("temp"),
        "feels_like": closest.get("feels_like"),
        "humidity": closest.get("humidity"),
        "wind": wind,
        "weather_id": weather.get("id"),
        "weather_main": weather.get("main"),
        "weather_description": weather.get("description"),
    }

def extract_weather_data_daily(weather_json, reference_timestamp):
    """Extracts the closest daily forecast and returns normalized daytime values."""

    if "daily" not in weather_json or not weather_json["daily"]:
        raise WeatherAPIException("Missing or empty 'daily' in daily forecast response")
    df = pd.DataFrame(weather_json["daily"])
    df["dt"] = pd.to_datetime(df["dt"], unit="s", utc=True)
    target_dt = pd.to_datetime(reference_timestamp, utc=True)
    df["time_diff"] = (df["dt"] - target_dt).abs()
    closest = df.loc[df["time_diff"].idxmin()]
    weather = closest.get("weather", [{}])[0]
    wind = compute_aggregated_wind(closest.get("wind_speed"), closest.get("wind_gust"))
    return {
        "lat": weather_json["lat"],
        "lon": weather_json["lon"],
        "dt": int(closest["dt"].timestamp()),
        "temp": closest.get("temp", {}).get("day"),
        "feels_like": closest.get("feels_like", {}).get("day"),
        "humidity": closest.get("humidity"),
        "wind": wind,
        "weather_id": weather.get("id"),
        "weather_main": weather.get("main"),
        "weather_description": weather.get("description"),
    }

def extract_weather_data_summary(weather_json, reference_timestamp):
    """Extracts summarized forecast values and infers conditions from pressure."""

    wind_data = weather_json.get("wind", {}).get("max", {})
    wind = compute_aggregated_wind(wind_data.get("speed"), None)
    temp = select_temp_from_summary(weather_json.get("temperature", {}), reference_timestamp)
    humidity = weather_json.get("humidity", {}).get("afternoon")
    pressure = weather_json.get("pressure", {}).get("afternoon")
    weather_id, weather_main, weather_description = infer_weather_conditions_from_pressure(pressure)
    return {
        "lat": weather_json["lat"],
        "lon": weather_json["lon"],
        "dt": int(pd.to_datetime(weather_json["date"]).timestamp()),
        "temp": temp,
        "feels_like": None,
        "humidity": humidity,
        "wind": wind,
        "weather_id": weather_id,
        "weather_main": weather_main,
        "weather_description": weather_description,
    }