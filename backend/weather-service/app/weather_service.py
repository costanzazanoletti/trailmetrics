import logging
import logging_setup
import json
import gzip
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from app.openweather_api_service import (
    fetch_weather_data, 
    generate_request_parameters,
    json_to_dataframe
    )
from app.kafka_producer import send_weather_output, send_retry_message
from app.exceptions import WeatherAPIException

logger = logging.getLogger("app")

# Load environment variables
load_dotenv()

# Get reference points parameters
GRID_SIZE = float(os.getenv("GRID_SIZE", "0.2"))
ELEVATION_THRESHOLD = float(os.getenv("ELEVATION_THRESHOLD", "600"))
TIME_THRESHOLD = float(os.getenv("TIME_THRESHOLD", "10800"))

def parse_kafka_segments(compressed_segments):
    """Parses the decompressed JSON segments into a DataFrame."""
    segments_list = decompress_segments(compressed_segments) 

    if not segments_list:
        print("No segments found") 
        return pd.DataFrame()
    
    df = pd.DataFrame(segments_list)
    return df
    
def decompress_segments(compressed_segments):
    """Decompresses Gzip-encoded activity segments."""
    try:
        decompressed = gzip.decompress(compressed_segments)
        return json.loads(decompressed.decode("utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error decompressing segments: {e}")
        return None

def add_datetime_columns(segments_df, activity_start_timestamp):
    """
    Adds start_date_time and end_date_time to segments_df based on activity start timestamp.
    """
    # Convert the activity start timestamp to a datetime object
    activity_start_dt = datetime.fromtimestamp(activity_start_timestamp, timezone.utc)
    
    # Create new columns with absolute datetime values
    segments_df["start_date_time"] = segments_df["start_time"].apply(lambda t: activity_start_dt + timedelta(seconds=t))
    segments_df["end_date_time"] = segments_df["end_time"].apply(lambda t: activity_start_dt + timedelta(seconds=t))
    
    return segments_df

def create_reference_points(df_segments, elevation_threshold, time_threshold, grid_size, use_time=True):
    """
    Creates reference points based on geographic location, elevation gain,
    and optionally time, using a grid-based approach to divide the area into bounding boxes.
    """
    selected_points = []

    # Initialize the first reference point
    first_lat, first_lng = df_segments.iloc[0]["start_lat"], df_segments.iloc[0]["start_lng"]
    last_time = df_segments.iloc[0]["start_date_time"] if use_time else None
    last_altitude = df_segments.iloc[0]["start_altitude"]

    selected_points.append({
        "lat": first_lat,
        "lng": first_lng,
        "timestamp": last_time,
        "altitude": last_altitude,
        "associated_segments": [df_segments.iloc[0]["segment_id"]]
    })

    last_lat = round(first_lat / grid_size) * grid_size
    last_lng = round(first_lng / grid_size) * grid_size

    for idx, row in df_segments.iloc[1:].iterrows():
        current_lat, current_lng = row["end_lat"], row["end_lng"]
        current_altitude = row["end_altitude"]
        current_time = row["end_date_time"] if use_time else None

        grid_lat = round(current_lat / grid_size) * grid_size
        grid_lng = round(current_lng / grid_size) * grid_size

        elevation_diff = abs(current_altitude - last_altitude)
        time_diff = (current_time - last_time).total_seconds() if use_time and last_time and current_time else 0

        grid_changed = grid_lat != last_lat or grid_lng != last_lng
        elevation_exceeded = elevation_diff >= elevation_threshold
        time_exceeded = use_time and time_diff >= time_threshold

        if grid_changed or elevation_exceeded or time_exceeded:
            selected_points.append({
                "lat": current_lat,
                "lng": current_lng,
                "timestamp": current_time,
                "altitude": current_altitude,
                "associated_segments": []
            })
            last_lat, last_lng = grid_lat, grid_lng
            last_altitude = current_altitude
            last_time = current_time if use_time else None

        selected_points[-1]["associated_segments"].append(row["segment_id"])

    return pd.DataFrame(selected_points)

def assign_weather_to_segments(segment_ids, weather_response_df):
    """
    Assigns weather data to each segment listed in associated_segments of reference_point.
    Directly maps weather data from the JSON response to the DataFrame columns.
    """
    
    # Create a new DataFrame with the segment IDs and broadcast the weather data across all segments
    weather_columns = weather_response_df.columns
    weather_data_repeated = pd.DataFrame([weather_response_df.iloc[0]] * len(segment_ids), columns=weather_columns)

    # Create a new DataFrame with segment_ids
    df_segments_ids = pd.DataFrame({"segment_id": segment_ids})

    # Combine the weather data with the segment_ids
    combined_df = pd.concat([df_segments_ids.reset_index(drop=True), weather_data_repeated.reset_index(drop=True)], axis=1)

    # Return the combined DataFrame with segment IDs and weather data
    return combined_df

def get_weather_info(activity_start_date, compressed_segments, activity_id):
    # Extract segments from kafka message
    segments_df = parse_kafka_segments(compressed_segments)
    # Add start and end timestamp to each segment
    segments_df = add_datetime_columns(segments_df, activity_start_date)

    # Create reference points
    reference_points_df = create_reference_points(segments_df, ELEVATION_THRESHOLD, TIME_THRESHOLD, GRID_SIZE)

    logger.info(f"Computed {len(reference_points_df)} reference points")

    for index, row in reference_points_df.iterrows():
        # Generate request parameters from each reference point
        request_params = generate_request_parameters(row)
        # Extract the segment_ids directly from reference_point's associated_segments
        segment_ids = row["associated_segments"]
        # Create an id for this block of segments
        reference_point_id = str(index + 1) + '_' + str(len(reference_points_df))
        # Call weather API and handle success and error response
        get_weather_data_from_api(activity_id, segment_ids, request_params, reference_point_id, retries = 0)

def get_weather_data_from_api(activity_id, segment_ids, request_params, reference_point_id, retries):
    try:
        # Fetch weather data from external API
        weather_response_json = fetch_weather_data(request_params)
        weather_response_df = json_to_dataframe(weather_response_json)

        # Assign weather data to segments
        weather_df = assign_weather_to_segments(segment_ids, weather_response_df)
        
        # If weather info is present, send Kafka message with weather info
        if not weather_response_df.empty:
            send_weather_output(activity_id, weather_df, reference_point_id)

    except WeatherAPIException as e:
        if e.status_code and e.status_code == 429:
            # Hit API request limit: publish retry message
            send_retry_message(activity_id, segment_ids, reference_point_id, request_params, retries)

def get_forecast_weather_info(start_date, duration, compressed_segments, activity_id):
    """
    Selects appropriate weather forecast API based on when the planned activity occurs.
    """
    segments_df = parse_kafka_segments(compressed_segments)
    
    if segments_df.empty:
        logger.warning(f"No segments found for planned activity {activity_id}")
        return
    # Add start and end timestamp to each segment
    segments_df = add_datetime_columns(segments_df, start_date)
    # Create reference points
    reference_points_df = create_reference_points(segments_df, ELEVATION_THRESHOLD, TIME_THRESHOLD, GRID_SIZE)
    
    # Compute start and end time of planned activity
    now = datetime.now(timezone.utc)
    start_dt = datetime.fromtimestamp(start_date, timezone.utc)
    end_dt = start_dt + timedelta(seconds=duration)
    logger.info(f"Planned activity {activity_id} from {start_dt} to {end_dt} (UTC)")
   
    # Forecast hourly 48h
    if end_dt <= now + timedelta(hours=48):
        logger.info("Using /onecall hourly forecast")

   
    # Forecast daily 8 days
    elif end_dt <= now + timedelta(days=8):
        logger.info("Using /onecall daily forecast")
        
    
    # Daily aggregation up to 1.5 years
    else:
        logger.info("Using /day_summary forecast (beyond 8 days)")

        
