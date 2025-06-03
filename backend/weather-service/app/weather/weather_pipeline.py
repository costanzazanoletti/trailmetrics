import pandas as pd
import logging
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from app.weather.segment_utils import parse_kafka_segments, add_datetime_columns, create_reference_points
from app.weather.weather_assignment import assign_weather_to_segments
from app.weather.weather_extraction import extract_weather_data
from app.api.openweather_api_service import fetch_weather_data, generate_request_parameters
from app.kafka_producer import send_weather_output, send_retry_message
from app.exceptions import WeatherAPIException

logger = logging.getLogger("app")
load_dotenv()

GRID_SIZE = float(os.getenv("GRID_SIZE", "0.2"))
ELEVATION_THRESHOLD = float(os.getenv("ELEVATION_THRESHOLD", "600"))
TIME_THRESHOLD = float(os.getenv("TIME_THRESHOLD", "10800"))

def choose_api_type(start_date, duration):
    """Choose the suitable API for the requested instant"""
    now = datetime.now(timezone.utc)
    start_dt = datetime.fromtimestamp(start_date, timezone.utc)
    end_dt = start_dt + timedelta(seconds=duration)
    if end_dt > now + timedelta(days=547):
        raise ValueError("Planned activity exceeds forecast availability (max 1.5 years ahead)")
    if start_dt < now:
        return "history"
    elif end_dt <= now + timedelta(hours=48):
        return "hourly"
    elif end_dt <= now + timedelta(days=8):
        return "daily"
    return "summary"

def get_weather_info(activity_start_date, activity_duration, compressed_segments, activity_id, is_planned=False):
    """
    Extracts the segments from Kafka message, creates reference points and gets the
    weather data from the suitable API.
    """
    segments_df = parse_kafka_segments(compressed_segments)
    segments_df = add_datetime_columns(segments_df, activity_start_date)
    reference_points_df = create_reference_points(segments_df, ELEVATION_THRESHOLD, TIME_THRESHOLD, GRID_SIZE, use_time=not is_planned)
    api_type = choose_api_type(activity_start_date, activity_duration)

    for index, row in reference_points_df.iterrows():
        request_params = generate_request_parameters(row, api_type)
        segment_ids = row["associated_segments"]
        reference_point_id = f"{index+1}_{len(reference_points_df)}"
        get_weather_data_from_api(api_type, activity_id, segment_ids, request_params, reference_point_id, retries=0)

def get_weather_data_from_api(api_type, activity_id, segment_ids, request_params, reference_point_id, retries):
    """
    Calls OpenWeather API and extracts the weather data. 
    Assigns weather data to segments.
    Sends Kafka message.
    """
    try:
        weather_response_json = fetch_weather_data(request_params, api_type)

        if api_type == "history":
            reference_timestamp = weather_response_json["data"][0]["dt"]
        elif api_type in ("hourly", "daily"):
            reference_timestamp = request_params["dt"]
        else:
            reference_timestamp = pd.to_datetime(weather_response_json["date"]).timestamp()

        weather_data_dict = extract_weather_data(api_type, weather_response_json, reference_timestamp)
        weather_response_df = pd.DataFrame([weather_data_dict])
        weather_df = assign_weather_to_segments(segment_ids, weather_response_df)

        if not weather_response_df.empty:
            send_weather_output(activity_id, weather_df, reference_point_id)
    except WeatherAPIException as e:
        if e.status_code == 429:
            send_retry_message(api_type, activity_id, segment_ids, reference_point_id, request_params, retries)