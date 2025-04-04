import logging
import logging_setup
import json
import gzip
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from app.openweather_api_service import fetch_weather_data, generate_request_parameters
from app.kafka_producer import send_weather_output, send_retry_message
from app.exceptions import WeatherAPIException

logger = logging.getLogger("app")

# Load environment variables
load_dotenv()

# Get reference points parameters
DISTANCE_THRESHOLD = float(os.getenv("DISTANCE_THRESHOLD", 1000))
ELEVATION_THRESHOLD = float(os.getenv("ELEVATION_THRESHOLD", 400))
TIME_THRESHOLD = float(os.getenv("TIME_THRESHOLD", 3600))

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

def create_reference_points(df_segments,  elevation_threshold, time_threshold, grid_size=0.1):
    """
    Creates reference points based on geographic location, time, and elevation gain,
    using a grid-based approach to divide the area into bounding boxes (default grid_size=0.1 degrees).
    """
    selected_points = []
    # Initialize the first reference point with rounded coordinates based on grid_size
    first_lat, first_lng = df_segments.iloc[0]["start_lat"], df_segments.iloc[0]["start_lng"]
    last_time = df_segments.iloc[0]["start_date_time"]
    last_altitude = df_segments.iloc[0]["start_altitude"]
    
    # Add the first reference point
    selected_points.append({
        "lat": first_lat,
        "lng": first_lng,
        "timestamp": last_time,
        "altitude": last_altitude,
        "associated_segments": [df_segments.iloc[0]["segment_id"]]
    })
    
    # Round first_lat and first_lng to compare
    last_lat = round(first_lat / grid_size) * grid_size  # Dynamic rounding based on grid_size
    last_lng = round(first_lng / grid_size) * grid_size
    
    # Iterate over the segments to find changes in coordinates, time, and elevation
    for idx, row in df_segments.iloc[1:].iterrows():
        current_lat, current_lng = row["end_lat"], row["end_lng"]
        current_time = row["end_date_time"]
        current_altitude = row["end_altitude"]

        # Check if there's a change in the grid location (bounding box), using grid_size for rounding
        grid_lat = round(current_lat / grid_size) * grid_size  # Dynamic rounding based on grid_size
        grid_lng = round(current_lng / grid_size) * grid_size
        
        # Calculate the time and elevation difference
        time_diff = (current_time - last_time).total_seconds()
        elevation_diff = abs(current_altitude - last_altitude)

        # If the reference point's grid or time threshold is exceeded, create a new reference point
        if (grid_lat != last_lat or grid_lng != last_lng or time_diff >= time_threshold or elevation_diff >= elevation_threshold):
            selected_points.append({
                "lat": current_lat,
                "lng": current_lng,
                "timestamp": current_time,
                "altitude": current_altitude,
                "associated_segments": []
            })
            last_lat, last_lng = grid_lat, grid_lng  # Update last position
            last_time = current_time  # Update last timestamp
            last_altitude = current_altitude  # Update last altitude

        # Associate the current segment to the closest reference point
        selected_points[-1]["associated_segments"].append(row["segment_id"])

    # Return a DataFrame for reference points, including associated segments
    reference_points_df = pd.DataFrame(selected_points)
    return reference_points_df

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
    reference_points_df = create_reference_points(segments_df, DISTANCE_THRESHOLD, ELEVATION_THRESHOLD, TIME_THRESHOLD)

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
        weather_response_df = fetch_weather_data(request_params)

        # Assign weather data to segments
        weather_df = assign_weather_to_segments(segment_ids, weather_response_df)
        
        # If weather info is present, send Kafka message with weather info
        if not weather_response_df.empty:
            send_weather_output(activity_id, weather_df, reference_point_id)

    except WeatherAPIException as e:
        if e.status_code and e.status_code == 429:
            # Hit API request limit: publish retry message
            send_retry_message(activity_id, segment_ids, reference_point_id, request_params, retries)