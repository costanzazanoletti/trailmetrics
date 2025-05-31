import logging
import logging_setup
import requests
import os
import pandas as pd
from dotenv import load_dotenv
import time
from app.counter_manager import RequestCounter
from app.exceptions import WeatherAPIException

logger = logging.getLogger("app")

# Load environment variables
load_dotenv()

# Get API parameters
OPENWEATHER_HISTORY_API_URL = os.getenv("OPENWEATHER_HISTORY_API_URL")
OPENWEATHER_ONECALL_API_URL = os.getenv("OPENWEATHER_ONECALL_API_URL")
OPENWEATHER_DAY_SUMMARY_API_URL = os.getenv("OPENWEATHER_DAY_SUMMARY_API_URL")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
DAILY_REQUEST_LIMIT = int(os.getenv("DAILY_REQUEST_LIMIT", 1000))

if not OPENWEATHER_API_KEY:
    raise ValueError("Weather API environment variables are not set properly")

# Global counter for requests
request_counter = RequestCounter(daily_limit=DAILY_REQUEST_LIMIT)

def generate_weather_variables_mapping():
    """
    Generates the mapping between weather variables returned by OpenWeather API and 
    corresponding DataFrame columns for the weather data extraction.
    """
    weather_variables = [
        { "name": "temp", "column": "temperature" },
        { "name": "feels_like", "column": "feels_like" },
        { "name": "pressure", "column": "pressure" },
        { "name": "humidity", "column": "humidity" },
        { "name": "dew_point", "column": "dew_point" },
        { "name": "clouds", "column": "cloudiness" },
        { "name": "uvi", "column": "uv_index" },
        { "name": "visibility", "column": "visibility" },
        { "name": "wind_speed", "column": "wind_speed" },
        { "name": "wind_gust", "column": "wind_gust" }, # optional
        { "name": "wind_deg", "column": "wind_deg" },
        { "name": "weather.id", "column": "weather_id" },
        { "name": "weather.description", "column": "weather_description" },
        { "name": "rain.1h", "column": "rain" },  # optional
        { "name": "snow.1h", "column": "snow" }  # optional
    ]

    weather_mapping = {}
    for var in weather_variables:
        weather_mapping[var["name"]] = var["column"]

    return weather_mapping, weather_variables

def generate_request_parameters(reference_point, api_type="history"):
    timestamp = int(reference_point["timestamp"].timestamp())
    coordinates = {"lat": reference_point["lat"], "lon": reference_point["lng"]}

    if api_type == "history":
        return {
            "lat": coordinates["lat"],
            "lon": coordinates["lon"],
            "dt": timestamp,
            "units": "metric"
        }
    elif api_type == "hourly":
        return {
            "lat": coordinates["lat"],
            "lon": coordinates["lon"],
            "exclude": "current,minutely,daily,alerts",
            "units": "metric"
        }
    elif api_type == "daily":
        return {
            "lat": coordinates["lat"],
            "lon": coordinates["lon"],
            "exclude": "current,minutely,hourly,alerts",
            "units": "metric"
        }
    elif api_type == "summary":
        date_str = reference_point["timestamp"].strftime("%Y-%m-%d")
        return {
            "lat": coordinates["lat"],
            "lon": coordinates["lon"],
            "date": date_str,
            "units": "metric"
        }
    else:
        raise ValueError("Unsupported API type")

def json_to_dataframe(response):
    # Flatten the data
    data = response['data'][0]
    
    # Extract the weather information and flatten it
    weather = data.get('weather', [{}])[0]
    
    # Get the wind values
    wind_speed = data.get('wind_speed', None)
    wind_gust = data.get('wind_gust', None)
    
    # Compute the aggregated wind value
    alpha = 0.7  # Adjust alpha to reflect the desired weighting
    if wind_speed is not None and wind_gust is not None:
        # If both wind_speed and wind_gust are available, calculate the weighted average
        aggregated_wind = (alpha * wind_speed) + ((1 - alpha) * wind_gust)
    elif wind_speed is not None:
        # If only wind_speed is available, use it directly
        aggregated_wind = wind_speed
    elif wind_gust is not None:
        # If only wind_gust is available, use it directly
        aggregated_wind = wind_gust
    else:
        # If both are None, set aggregated_wind to None
        aggregated_wind = None
    # Limit the aggregated wind to 2 decimal places
    if aggregated_wind is not None:
        aggregated_wind = round(aggregated_wind, 2)


    # Create a dictionary for the DataFrame columns with only necessary data
    data_dict = {
        'lat': response['lat'],
        'lon': response['lon'],
        'dt': data['dt'],
        'temp': data.get('temp', None),
        'feels_like': data.get('feels_like', None),
        'humidity': data.get('humidity', None),
        'wind': aggregated_wind,  
        'weather_id': weather.get('id', None),
        'weather_main': weather.get('main', None),
        'weather_description': weather.get('description', None)
    }

    # Convert to DataFrame
    df = pd.DataFrame([data_dict])
    
    return df

def fetch_weather_data(params, api_type="history"):
    global request_counter
    logger.info(f"Request counter: {request_counter.get_count()}")

    try:
        request_counter.increment()
    except Exception:
        logger.warning(f"Daily limit of {DAILY_REQUEST_LIMIT} requests reached.")
        raise WeatherAPIException("Daily request limit reached", status_code=429)

    params["appid"] = OPENWEATHER_API_KEY

    if api_type == "history":
        url = OPENWEATHER_HISTORY_API_URL
    elif api_type == "hourly" or api_type == "daily":
        url = OPENWEATHER_ONECALL_API_URL
    elif api_type == "summary":
        url = OPENWEATHER_DAY_SUMMARY_API_URL
    else:
        raise ValueError("Unsupported API type")

    try:
        logger.info(f"Requesting weather data for {params.get('lat')}, {params.get('lon')} with API type: {api_type}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        logger.info(f"Weather data received")
        time.sleep(1)
        return response.json()

    except requests.exceptions.HTTPError as err:
        if response is not None and response.status_code == 429:
            logger.warning("Weather API rate limit exceeded.")
            raise WeatherAPIException("Hourly request limit reached", status_code=429)
        else:
            logger.error(f"Request HTTP error: {err}")
            raise WeatherAPIException(f"HTTP Error: {err}", status_code=response.status_code)

    except requests.exceptions.RequestException as err:
        logger.error(f"Request error: {err}")
        raise WeatherAPIException(f"Request failed: {err}")


