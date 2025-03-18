import logging
import logging_setup
import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

logger = logging.getLogger("app")

# Load environment variables
load_dotenv()

# Get API parameters
WEATHER_HISTORY_API_URL=os.getenv("WEATHER_HISTORY_API_URL")
API_KEY=os.getenv("API_KEY")
if not all([WEATHER_HISTORY_API_URL, API_KEY]):
    raise ValueError("Weather API environment variables are not set properly")

def round_request_time(reference_points_df):
    """
    Adjusts the request time range to include the previous and next full hour.
    """
    # Retrieve the first and last timestamps from the reference points DataFrame
    from_datetime = reference_points_df.iloc[0]["start_date_time"]
    until_datetime = reference_points_df.iloc[-1]["end_date_time"]

    # Round down from_time to the previous full hour
    from_datetime = from_datetime.replace(minute=0, second=0, microsecond=0)

    # Round up until_time to the next full hour
    if until_datetime.minute > 0 or until_datetime.second > 0:
        until_datetime = until_datetime.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    # Convert back to ISO 8601 format
    from_time = from_datetime.isoformat() + "Z"
    until_time = until_datetime.isoformat() + "Z"

    return from_time, until_time

def generate_variables_mapping():
    """
    Generates the mapping between weather variables required for the request and corresponding DataFrame columns.
    """
    # Define the weather variables and their corresponding API names
    variables = [
        { "name": "APTMP", "level": "2 m above ground", "info":"", "column": "temperature" },
        { "name": "RH", "level": "2 m above ground", "info":"", "column": "humidity" },
        { "name": "APCP", "level": "surface", "info":"", "column": "precipitation" },
        { "name": "CRAIN", "level": "surface", "info":"", "column": "rain" },
        { "name": "CSNOW", "level": "surface", "info":"", "column": "snow" },
        { "name": "SOILL", "level": "0-0.1 m below ground", "info":"", "column": "soil_moisture" },
        { "name": "SOTYP", "level": "surface", "info":"", "column": "soil_type" },
        { "name": "UGRD", "level": "10 m above ground", "info":"", "column": "u_wind" },
        { "name": "VGRD", "level": "10 m above ground", "info":"", "column": "v_wind" },
        { "name": "GUST", "level": "surface", "info":"", "column": "wind_gust" }
    ]

    # Map the variables to a dictionary for easy access
    weather_mapping = {}
    for var in variables:
        # Construct the full parameter name for the API
        param_name = f"{var['name']}|{var['level']}|{var['info']}"
        # Map the API parameter to the corresponding DataFrame column
        weather_mapping[param_name] = var['column']

    return weather_mapping, variables

def generate_request_parameters(reference_points_df):
    """Generates request parameters for the weather API request considering activity start time."""

    # Compute absolute timestamps by adding activity start timestamp
    from_time, until_time = round_request_time(reference_points_df)
    
    # Convert fromTime and untilTime back to timestamps for calculating horizon
    from_timestamp = datetime.fromisoformat(from_time[:-1]).timestamp()
    until_timestamp = datetime.fromisoformat(until_time[:-1]).timestamp()

    # Compute minHorizon and maxHorizon based on rounded timestamps
    min_horizon = 0
    max_horizon = max(6, int((until_timestamp - from_timestamp) // 3600))  # At least 6 hours

    # Extract coordinates
    coordinates = [
        {"lat": row["lat"], "lon": row["lng"]}
        for _, row in reference_points_df.iterrows()
    ]

    # Genera il mapping e la lista delle variabili meteo
    _, variables = generate_variables_mapping()

    # Build request parameters
    request_params = {
        "fromTime": from_time,
        "untilTime": until_time,
        "minHorizon": min_horizon,
        "maxHorizon": max_horizon,
        "coordinates": coordinates,
        "variables": variables
    }

    return request_params

def fetch_weather_data(reference_points_df):
    """
    Prepares and sends a request to the weather API and retrieves the forecast data.
    """
    # Create request payload
    request_payload = generate_request_parameters(reference_points_df)

    # Define request headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
        "Accept-Encoding": "gzip",
        "Accept": "application/json"
    }
    # Perform request
    try:
        response = requests.post(WEATHER_HISTORY_API_URL, json=request_payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        return response.json()  # Return the JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None