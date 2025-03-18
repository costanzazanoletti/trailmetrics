import logging
import logging_setup
import json
import gzip
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from geopy.distance import geodesic
from dotenv import load_dotenv
from app.weather_api_service import fetch_weather_data, generate_variables_mapping

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
    activity_start_dt = datetime.utcfromtimestamp(activity_start_timestamp)
    
    # Create new columns with absolute datetime values
    segments_df["start_date_time"] = segments_df["start_time"].apply(lambda t: activity_start_dt + timedelta(seconds=t))
    segments_df["end_date_time"] = segments_df["end_time"].apply(lambda t: activity_start_dt + timedelta(seconds=t))
    
    return segments_df

def create_reference_points(df_segments, distance_threshold, elevation_threshold, time_threshold):
    """
    Selects reference points for weather requests based on distance, elevation gain, and time intervals.
    Copies start_date_time and end_date_time directly from the original segment data.
    """

    # Initialize the list of points with the first segment
    selected_points = [
        (df_segments.iloc[0]["start_lat"],
         df_segments.iloc[0]["start_lng"],
         df_segments.iloc[0]["start_distance"],
         df_segments.iloc[0]["end_distance"],
         df_segments.iloc[0]["start_altitude"],
         df_segments.iloc[0]["end_altitude"],
         df_segments.iloc[0]["start_date_time"],  # Copy actual timestamps
         df_segments.iloc[0]["end_date_time"],
         0,  # Distance traveled (first point has 0)
         0,  # Time elapsed (first point has 0)
         0)  # Elevation change (first point has 0)
    ]

    # Reference variables for tracking the last selected point
    last_distance = df_segments.iloc[0]["end_distance"]
    last_altitude = df_segments.iloc[0]["end_altitude"]
    last_time = df_segments.iloc[0]["end_date_time"]

    # Iterate over segments to determine weather request points
    for index, row in df_segments.iterrows():
        current_distance = row["end_distance"]
        current_lat, current_lng = row["end_lat"], row["end_lng"]
        current_altitude = row["end_altitude"]
        current_time = row["end_date_time"]

        # Compute the changes since the last selected point
        distance_traveled = current_distance - last_distance
        elevation_change = abs(current_altitude - last_altitude)
        time_elapsed = (current_time - last_time).total_seconds()  # Ensure time is in seconds

        # If any of the thresholds are exceeded, add a new reference point
        if (distance_traveled >= distance_threshold or
            elevation_change >= elevation_threshold or
            time_elapsed >= time_threshold):

            selected_points.append((current_lat, current_lng, last_distance, current_distance,
                                    last_altitude, current_altitude, last_time, current_time,
                                    distance_traveled, time_elapsed, elevation_change))

            # Update reference variables
            last_distance = current_distance
            last_altitude = current_altitude
            last_time = current_time

    # Always add the final point of the activity
    final_distance = df_segments.iloc[-1]["end_distance"] - last_distance
    final_time = (df_segments.iloc[-1]["end_date_time"] - last_time).total_seconds()
    final_elevation = abs(df_segments.iloc[-1]["end_altitude"] - last_altitude)

    selected_points.append(
        (df_segments.iloc[-1]["end_lat"],
         df_segments.iloc[-1]["end_lng"],
         df_segments.iloc[-1]["start_distance"],
         df_segments.iloc[-1]["end_distance"],
         df_segments.iloc[-1]["start_altitude"],
         df_segments.iloc[-1]["end_altitude"],
         df_segments.iloc[-1]["start_date_time"],
         df_segments.iloc[-1]["end_date_time"],
         final_distance,
         final_time,
         final_elevation
        ))

    # Create a DataFrame to display the selected points
    return pd.DataFrame(selected_points, columns=[
        "lat", "lng", "start_distance", "end_distance", "start_altitude", "end_altitude",
        "start_date_time", "end_date_time", "distance_traveled", "time_elapsed", "elevation_change"
    ])

def assign_weather_to_segments(df_segments, weather_response):
    """
    Assigns weather data to each segment based on the closest matching time and location.
    """
    # Get response variables to column mapping
    weather_mapping, _ = generate_variables_mapping()

    # Initialize new columns in df_segments for weather data based on weather_mapping
    for column in weather_mapping.values():
        df_segments[column] = None  # Dynamically initialize columns based on weather_mapping

    # Ensure segment start_date_time is also timezone-naive
    df_segments["start_date_time"] = pd.to_datetime(df_segments["start_date_time"]).dt.tz_localize(None)

    # If weather_response is None or empty, log a warning and return the DataFrame as is
    if not weather_response:
        logging.warning("Weather response is empty or None, no weather data assigned.")
        return df_segments  

    # Convert forecasted_time to datetime and make it timezone-naive    
    for entry in weather_response:
        entry["forecasted_time"] = pd.to_datetime(entry["forecasted_time"]).tz_localize(None)

    # Iterate over each segment
    for index, segment in df_segments.iterrows():
        segment_time = segment["start_date_time"]
        segment_coords = (segment["start_lat"], segment["start_lng"])

        # Find the closest weather data in time
        closest_time_entry = min(
            weather_response,
            key=lambda w: abs((w["forecasted_time"] - segment_time).total_seconds())
        )
        closest_time = closest_time_entry["forecasted_time"]

        # Filter weather entries that match this closest timestamp
        matching_time_entries = [w for w in weather_response if w["forecasted_time"] == closest_time]
        
        # Find the closest weather data in location among these matching time entries
        closest_weather = min(
            matching_time_entries,
            key=lambda w: geodesic(segment_coords, (w["lat"], w["lon"])).meters
        )

       # Log for debugging: Check if closest_weather contains expected data
        logging.debug(f"Closest weather data for segment {index}: {closest_weather}")

        # Assign the closest weather data to the segment using the mapping
        for api_param, column in weather_mapping.items():
            value = closest_weather.get(api_param, None)
            df_segments.at[index, column] = value  # Assign the value to the column

            # Log if a value was not found for the API parameter
            if value is None:
                logging.warning(f"Weather parameter {api_param} not found for segment {index}")
    return df_segments

def get_weather_info(activity_start_date, compressed_segments):
    # Extract segments from kafka message
    segments_df = parse_kafka_segments(compressed_segments)
    # Add start and end timestamp to each segment
    segments_df = add_datetime_columns(segments_df, activity_start_date)

    # Create reference points
    reference_points_df = create_reference_points(segments_df, DISTANCE_THRESHOLD, ELEVATION_THRESHOLD, TIME_THRESHOLD)
    logger.info(f"Computed {len(reference_points_df)} reference points")

    # Fetch weather data from external API
    weather_response = fetch_weather_data(reference_points_df)

    # Assign weather data to segments (HANDLE EMPTY RESPONSE)
    return assign_weather_to_segments(segments_df, weather_response)

      