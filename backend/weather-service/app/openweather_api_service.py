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

def generate_request_parameters(reference_point):
    """Generates request parameters for the weather API request considering activity start time."""

    timestamp = int(reference_point["timestamp"].timestamp())  # Convert to Unix timestamp
    coordinates = {"lat": reference_point["lat"], "lon": reference_point["lng"]}

    return {
        "lat": coordinates["lat"],
        "lon": coordinates["lon"],
        "dt": timestamp,
        "units": "metric",  
        "appid": OPENWEATHER_API_KEY  
    }

def json_to_dataframe(response):
    # Flatten the data
    data = response['data'][0]
    
    # Extract the weather information and flatten it
    weather = data.get('weather', [{}])[0]
    
    # Create a dictionary for the DataFrame columns
    data_dict = {
        'lat': response['lat'],
        'lon': response['lon'],
        'timezone': response['timezone'],
        'timezone_offset': response['timezone_offset'],
        'dt': data['dt'],
        'sunrise': data.get('sunrise', None),  # Corrected line
        'sunset': data.get('sunset', None),  # Corrected line
        'temp': data.get('temp', None),  # Corrected line
        'feels_like': data.get('feels_like', None),  # Corrected line
        'pressure': data.get('pressure', None),  # Corrected line
        'humidity': data.get('humidity', None),  # Corrected line
        'dew_point': data.get('dew_point', None),  # Corrected line
        'uvi': data.get('uvi', None),  # Corrected line
        'clouds': data.get('clouds', None),  # Corrected line
        'visibility': data.get('visibility', None),  # Corrected line
        'wind_speed': data.get('wind_speed', None),  # Corrected line
        'wind_deg': data.get('wind_deg', None),  # Corrected line
        'wind_gust': data.get('wind_gust', None),  # Corrected line
        'weather_id': weather.get('id', None),
        'weather_main': weather.get('main', None),
        'weather_description': weather.get('description', None),
        'weather_icon': weather.get('icon', None),
        'rain_1h': data.get('rain', {}).get('1h', None),  # Ensure rain and snow also show None if missing
        'snow_1h': data.get('snow', {}).get('1h', None)
    }


    # Convert to DataFrame
    df = pd.DataFrame([data_dict])
    
    return df

def fetch_weather_data(params):
    """
    Sends requests to the weather API and retrieves the forecast data.
    """
    # Daily request counter
    global request_counter
    logger.info(f"Request counter: {request_counter.get_count()}")

    # Increment request counter
    try:
        request_counter.increment()
    except Exception as e:
        # If unable to increment counter, raise an exception
        logger.warning(f"Daily limit of {DAILY_REQUEST_LIMIT} requests reached.")
        raise WeatherAPIException("Daily request limit reached", status_code=429, retry_in_hour=False) 
    
    try: 
        # Perform the request to the OpenWeather API
        logger.info(f"Requesting weather data for {params['lat']}, {params['lon']} at {params['dt']}")
        response = requests.get(OPENWEATHER_HISTORY_API_URL, params=params)  
        # Raise an exception for non-OK status codes
        response.raise_for_status()  

        # If the request is successful, process the data
        logger.info(f"Weather data received")
        time.sleep(1)  # Ensure at least 1 second between requests
        return json_to_dataframe(response.json())  # Return the API response as a DataFrame
        
    except requests.exceptions.HTTPError as err:  
        if response is not None and response.status_code == 429: # Rate limit exceeded
            logger.warning(f"Weather API rate limit exceeded.")
            raise WeatherAPIException("Hourly request limit reached", status_code=429, retry_in_hour=True)
        else:
            logger.error(f"Request HTTP error: {err}")
            raise WeatherAPIException(f"HTTP Error: {err}", status_code=response.status_code)
        
    except requests.exceptions.RequestException as err:
        logger.error(f"Request error: {err}")
        raise WeatherAPIException(f"Request failed: {err}")


