import os
import json
import gzip
import logging
import logging_setup
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger("app")

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
    """Preprocesses DataFrame: cleans, interpolates, and fixes missing lat/lng values."""
    
    # Check for missing required columns
    required_columns = ["distance", "altitude", "latlng", "cadence", "grade_smooth", "velocity_smooth", "time"]
    missing_columns = [col for col in required_columns if col not in df.columns or df[col].isnull().all()]
    if missing_columns:
        logger.error(f"Missing required columns for Activity {activity_id}: {missing_columns}")
        return None
    
    # Ensure heartrate column exists, if not, create it with NaN values
    if "heartrate" not in df.columns:
        logger.warning(f"Missing 'heartrate' data for Activity {activity_id}. Setting 'heartrate' to None.")
        df["heartrate"] = None

    # Remove rows with time o distance NaN
    df.dropna(subset=["time", "distance"], inplace=True)

    # Rename columns 
    df.rename(columns={"grade_smooth": "grade", "velocity_smooth": "speed"}, inplace=True)

    # Convert columns to numeric to avoid interpolation warning
    numeric_columns = ["altitude", "grade", "speed", "cadence", "heartrate"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')  # Convert to numeric, coercing errors to NaN

    # Interpolate missing numerical values
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].interpolate(method="linear", limit_direction="both")

    # Handle latlng: fill null value and interpolate if necessary
    for i in range(len(df)):

        if (
            len(df.loc[i, "latlng"]) == 0 or 
            (i > 0 and tuple(df.loc[i, "latlng"]) == tuple(df.loc[i-1, "latlng"]) and df.loc[i, "distance"] != df.loc[i-1, "distance"])
        ):
        
            logger.info(f"Fixing latlng at index {i}, distance: {df.loc[i, 'distance']}")

            # If the previous point has identical distance, copy the coordinates
            if i > 0 and df.loc[i, "distance"] == df.loc[i-1, "distance"]:
                logger.info(f"Copying from previous point at index {i-1}")
                df.at[i, "latlng"] = df.loc[i-1, "latlng"]

            # If the following point has identical distance, copy the coordinates
            elif i < len(df) - 1 and df.loc[i, "distance"] == df.loc[i+1, "distance"]:
                logger.info(f"Copying from following point at index {i+1}")
                df.at[i, "latlng"] = df.loc[i+1, "latlng"]

            # If nor the previous nor the following point have the same distance, interpolate
            else:
                j = i + 1
                while j < len(df) and (np.array_equal(df.loc[j, "latlng"], df.loc[i, "latlng"])):

                    j += 1  # Find the first valid following point
                
                if j < len(df):  # If we find a valid point
                    
                    logger.info(f"Interpolating between index {i-1} and {j}")

                    lat_start, lng_start = df.loc[i-1, "latlng"]
                    lat_end, lng_end = df.loc[j, "latlng"]
                    dist_start = df.loc[i-1, "distance"]
                    dist_end = df.loc[j, "distance"]

                    for k in range(i, j):  # Interpolate all the points in the block
                        alpha = (df.loc[k, "distance"] - dist_start) / (dist_end - dist_start) if dist_end != dist_start else 0
                        lat_interp = lat_start + alpha * (lat_end - lat_start)
                        lng_interp = lng_start + alpha * (lng_end - lng_start)
                        df.at[k, "latlng"] = [lat_interp, lng_interp]
        
                else:
                    logger.info(f"No valid next point found for index {i}, copying previous")
                    df.at[i, "latlng"] = df.loc[i-1, "latlng"]  # Copy the last valid point

    # Compute cumulated ascent and descent
    altitude_diff = df["altitude"].diff().fillna(0)
    df["ascent_so_far"] = altitude_diff.clip(lower=0).cumsum()
    df["descent_so_far"] = -altitude_diff.clip(upper=0).cumsum()
    
    return df.reset_index(drop=True)

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
                "end_lng": df["latlng"].iloc[i - 1][1],
                "start_altitude": df["altitude"].iloc[start_index],
                "end_altitude": df["altitude"].iloc[i - 1],
                "start_time": df["time"].iloc[start_index],
                "end_time": df["time"].iloc[i - 1],
                "start_heartrate": df["heartrate"].iloc[start_index] if df["heartrate"].iloc[start_index] is not None else np.nan,  # Handle missing heartrate
                "end_heartrate": df["heartrate"].iloc[i - 1] if df["heartrate"].iloc[i - 1] is not None else np.nan,  # Handle missing heartrate
                "avg_heartrate": np.nanmean(df["heartrate"].iloc[start_index:i]) if df["heartrate"].iloc[start_index:i].notna().any() else np.nan,  # Use nanmean to handle NaN values
                "cumulative_ascent": df["ascent_so_far"].iloc[start_index],
                "cumulative_descent": df["descent_so_far"].iloc[start_index],
            }

            segments.append(segment)
            start_index = i
    final_segments_df = pd.DataFrame(segments) if segments else pd.DataFrame()
    return final_segments_df

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

def parse_planned_activity(compressed_stream, activity_id):
    """
    Parses a planned activity stream and returns a DataFrame with latlng, altitude, distance, grade, ascent and descent.
    Assumes distance and grade are already present in the stream.
    """
    stream_list = decompress_stream(compressed_stream)
    if not stream_list:
        return pd.DataFrame()

    try:
        stream_dict = {entry["type"]: entry["data"] for entry in stream_list}
        latlng = stream_dict.get("latlng", [])
        altitude = stream_dict.get("altitude", [])
        distance = stream_dict.get("distance", [])
        grade = stream_dict.get("grade_smooth", [])

        if not (latlng and altitude and distance and grade):
            logger.error(f"Incomplete stream data for Activity {activity_id}")
            return pd.DataFrame()

        if not (len(latlng) == len(altitude) == len(distance) == len(grade)):
            logger.error(f"Stream length mismatch for Activity {activity_id}")
            return pd.DataFrame()

        df = pd.DataFrame({
            "latlng": latlng,
            "altitude": altitude,
            "distance": distance,
            "grade": grade,
            "activity_id": activity_id
        })

        df[["lat", "lon"]] = pd.DataFrame(df["latlng"].tolist(), index=df.index)

        # Compute cumulated ascent and descent
        altitude_diff = df["altitude"].diff().fillna(0)
        df["ascent_so_far"] = altitude_diff.clip(lower=0).cumsum()
        df["descent_so_far"] = -altitude_diff.clip(upper=0).cumsum()

        return df

    except Exception as e:
        logger.error(f"Error parsing planned activity stream for Activity {activity_id}: {e}")
        return pd.DataFrame()

def create_planned_segments(df, activity_id, config):
    """Segments a planned activity"""

    if config["rolling_window_size"] > 1:
        df["grade"] = df["grade"].rolling(window=config["rolling_window_size"], center=True, min_periods=1).mean()

    segments, start_index = [], 0
    for i in range(1, len(df)):
        segment_length = df["distance"].iloc[i] - df["distance"].iloc[start_index]
        grade_change = abs(df["grade"].iloc[i] - df["grade"].iloc[i - 1])

        if (grade_change > config["gradient_tolerance"] and segment_length >= config["min_segment_length"]) or segment_length > config["max_segment_length"]:
            elev_diff = df["altitude"].iloc[i - 1] - df["altitude"].iloc[start_index]
            avg_grade = (elev_diff / segment_length * 100) if segment_length > 0 else 0
            avg_cadence = None
            movement_type = None
            avg_heartrate = None
            start_heartrate = None
            end_heartrate = None

            segment = {
                "activity_id": activity_id,
                "start_distance": df["distance"].iloc[start_index],
                "end_distance": df["distance"].iloc[i - 1],
                "segment_length": segment_length,
                "avg_gradient": avg_grade,
                "avg_cadence": avg_cadence,
                "movement_type": movement_type,
                "type": "uphill" if avg_grade > 0 else "downhill" if avg_grade < 0 else "flat",
                "grade_category": round(avg_grade / config["classification_tolerance"]) * config["classification_tolerance"],
                "start_lat": df["lat"].iloc[start_index],
                "start_lng": df["lon"].iloc[start_index],
                "end_lat": df["lat"].iloc[i - 1],
                "end_lng": df["lon"].iloc[i - 1],
                "start_altitude": df["altitude"].iloc[start_index],
                "end_altitude": df["altitude"].iloc[i - 1],
                "start_time": None,
                "end_time": None,
                "start_heartrate": start_heartrate,
                "end_heartrate": end_heartrate,
                "avg_heartrate": avg_heartrate,
                "cumulative_ascent": df["ascent_so_far"].iloc[start_index],
                "cumulative_descent": df["descent_so_far"].iloc[start_index],
            }
            segments.append(segment)
            start_index = i
    
    return pd.DataFrame(segments) if segments else pd.DataFrame()

def segment_planned_activity(activity_id, compressed_stream, duration):
    """Segments a planned activity using latlng and altitude only, and estimates time per segment."""
    logger.info(f"Processing Planned Activity {activity_id}")
    config = load_config()
    df = parse_planned_activity(compressed_stream, activity_id)
    if df.empty:
        return df

    segments_df = create_planned_segments(df, activity_id, config)
    if segments_df.empty:
        return segments_df

    # Estimates duration of each segment proportional to total length
    total_length = segments_df["segment_length"].sum()
    if total_length == 0:
        logger.warning(f"Total segment length is zero for planned activity {activity_id}")
        return pd.DataFrame()

    segments_df["duration"] = segments_df["segment_length"] / total_length * duration
    segments_df["start_time"] = segments_df["duration"].cumsum().shift(fill_value=0)
    segments_df["end_time"] = segments_df["start_time"] + segments_df["duration"]

    return segments_df
