import json
import gzip
import pandas as pd
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger("app")

def parse_kafka_segments(compressed_segments):
    """Decompress and convert to DataFrame segments from Kafka message"""
    segments_list = decompress_segments(compressed_segments) 
    if not segments_list:
        logger.warning("No segments found") 
        return pd.DataFrame()
    return pd.DataFrame(segments_list)

def decompress_segments(compressed_segments):
    """Decompress segments"""
    try:
        decompressed = gzip.decompress(compressed_segments)
        return json.loads(decompressed.decode("utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error decompressing segments: {e}")
        return None

def add_datetime_columns(segments_df, activity_start_timestamp):
    """Add start datetime and end datetime to all segments based on activity start date"""
    activity_start_dt = datetime.fromtimestamp(activity_start_timestamp, timezone.utc)
    segments_df["start_date_time"] = segments_df["start_time"].apply(lambda t: activity_start_dt + timedelta(seconds=t))
    segments_df["end_date_time"] = segments_df["end_time"].apply(lambda t: activity_start_dt + timedelta(seconds=t))
    return segments_df

def create_reference_points(df_segments, elevation_threshold, time_threshold, grid_size, use_time=True):
    """
    Generates reference points from a list of activity segments based on spatial grid, elevation change,
    and optionally time gaps. Each reference point groups nearby segments to minimize redundant weather API calls.
    """

    selected_points = []
    first_lat, first_lng = df_segments.iloc[0]["start_lat"], df_segments.iloc[0]["start_lng"]
    last_time = df_segments.iloc[0]["start_date_time"]
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

    for _, row in df_segments.iloc[1:].iterrows():
        current_lat, current_lng = row["end_lat"], row["end_lng"]
        current_altitude = row["end_altitude"]
        current_time = row["end_date_time"]

        grid_lat = round(current_lat / grid_size) * grid_size
        grid_lng = round(current_lng / grid_size) * grid_size

        elevation_diff = abs(current_altitude - last_altitude)
        time_diff = (current_time - last_time).total_seconds() if use_time and last_time and current_time else 0

        if grid_lat != last_lat or grid_lng != last_lng or elevation_diff >= elevation_threshold or (use_time and time_diff >= time_threshold):
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
    
    reference_df = pd.DataFrame(selected_points)
    logger.info(f"Created {len(reference_df)} reference points (use_time={use_time})")
    return pd.DataFrame(selected_points)