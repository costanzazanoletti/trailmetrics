import os
import json
import gzip
import logging
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger("segmentation")

# Load environment variables
load_dotenv()

def load_config():
    """Loads configuration parameters from environment variables."""
    return {
        "gradient_tolerance": float(os.getenv("GRADIENT_TOLERANCE", 0.5)),
        "min_segment_length": float(os.getenv("MIN_SEGMENT_LENGTH", 50.0)),
        "max_segment_length": float(os.getenv("MAX_SEGMENT_LENGTH", 200.0)),
        "classification_tolerance": float(os.getenv("CLASSIFICATION_TOLERANCE", 2.5)),
        "cadence_threshold": int(os.getenv("CADENCE_THRESHOLD", 60)),
        "cadence_tolerance": int(os.getenv("CADENCE_TOLERANCE", 5)),
        "rolling_window_size": int(os.getenv("ROLLING_WINDOW_SIZE", 0))
    }

def decompress_stream(compressed_stream):
    """Decompresses Gzip-encoded activity stream."""
    try:
        return json.loads(gzip.decompress(compressed_stream).decode("utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error decompressing stream: {e}")
        return None

def parse_kafka_stream(compressed_stream, activity_id):
    """Parses the decompressed JSON activity stream into a DataFrame."""
    stream_list = decompress_stream(compressed_stream)
    if not stream_list:
        return pd.DataFrame()
    
    try:
        stream_dict = {entry["type"]: entry["data"] for entry in stream_list}
        expected_fields = ["latlng", "velocity_smooth", "grade_smooth", "cadence",
                           "heartrate", "altitude", "distance", "time"]
        for field in expected_fields:
            if field not in stream_dict:
                stream_dict[field] = [np.nan] * len(next(iter(stream_dict.values()), []))

        df = pd.DataFrame(stream_dict)
        df["activity_id"] = activity_id
        return df
    except Exception as e:
        logger.error(f"Error parsing Kafka stream for Activity {activity_id}: {e}")
        return pd.DataFrame()

def preprocess_streams(df, activity_id):
    """Preprocesses DataFrame: renames columns, fills missing values."""
    required_columns = ["distance", "altitude", "latlng", "cadence", "grade_smooth", "velocity_smooth", "time"]
    missing_columns = [col for col in required_columns if col not in df.columns or df[col].isnull().all()]
    if missing_columns:
        logger.error(f"Missing required columns for Activity {activity_id}: {missing_columns}")
        return None
    
    df = df.rename(columns={"grade_smooth": "grade", "velocity_smooth": "speed"})
    df.ffill(inplace=True)
    return df

def create_segments(df, activity_id, config):
    """Segments an activity based on gradient and cadence changes."""
    df.sort_values("distance", inplace=True)
    if config["rolling_window_size"] > 1:
        df["grade"] = df["grade"].rolling(window=config["rolling_window_size"], center=True, min_periods=1).mean()
        df["cadence"] = df["cadence"].rolling(window=config["rolling_window_size"], center=True, min_periods=1).mean()
    
    segments, start_index = [], 0
    for i in range(1, len(df)):
        segment_length = df["distance"].iloc[i] - df["distance"].iloc[start_index]
        grade_change = abs(df["grade"].iloc[i] - df["grade"].iloc[i - 1])
        cadence_change = abs(df["cadence"].iloc[i] - df["cadence"].iloc[i - 1])
        
        if ((grade_change > config["gradient_tolerance"] or cadence_change > config["cadence_tolerance"]) and 
            segment_length >= config["min_segment_length"]) or segment_length > config["max_segment_length"]:
            segment = {
                "activity_id": activity_id,
                "start_distance": df["distance"].iloc[start_index],
                "end_distance": df["distance"].iloc[i - 1],
                "segment_length": segment_length,
                "avg_gradient": np.mean(df["grade"].iloc[start_index:i]),
                "avg_cadence": np.mean(df["cadence"].iloc[start_index:i]),
                "movement_type": "running" if np.mean(df["cadence"].iloc[start_index:i]) > config["cadence_threshold"] else "walking",
                "type": "uphill" if np.mean(df["grade"].iloc[start_index:i]) > 0 else "downhill" if np.mean(df["grade"].iloc[start_index:i]) < 0 else "flat",
                "grade_category": round(np.mean(df["grade"].iloc[start_index:i]) / config["classification_tolerance"]) * config["classification_tolerance"],
                "start_lat": df["latlng"].iloc[start_index][0],
                "start_lng": df["latlng"].iloc[start_index][1],
                "end_lat": df["latlng"].iloc[i - 1][0],
                "end_lng": df["latlng"].iloc[i - 1][1]
            }
            segments.append(segment)
            start_index = i
    
    return pd.DataFrame(segments) if segments else pd.DataFrame()

def segment_activity(activity_id, compressed_stream):
    """Main function to process and segment an activity."""
    logger.info(f"Processing Activity {activity_id}")
    config = load_config()
    df = parse_kafka_stream(compressed_stream, activity_id)
    if df.empty:
        return df
    
    df = preprocess_streams(df, activity_id)
    if df is None:
        return pd.DataFrame()
    
    return create_segments(df, activity_id, config)
