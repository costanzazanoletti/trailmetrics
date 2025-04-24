import logging
import logging_setup
import json
import gzip
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from app.exceptions import DatabaseException
from database import segments_batch_insert_and_update_status, delete_all_data_by_activity_ids
from app.utilities import parse_compressed_data

logger = logging.getLogger("app")

# Load environment variables
load_dotenv()
EFFICIENCY_FACTOR_SCALE=float(os.getenv("EFFICIENCY_FACTOR_SCALE", "10.0"))
EFFICIENCY_ELEVATION_WEIGHT=float(os.getenv("EFFICIENCY_FACTOR_SCALE", "1.0"))
EFFICIENCY_FACTOR_HR_DRIFT_WEIGHT=float(os.getenv("EFFICIENCY_FACTOR_SCALE", "1.0"))

def process_segments(activity_id, user_id, compressed_segments, engine):
    """Processes segments and compute efficiency metrics and score"""
    try:
        # Extract segments DataFrame from Kafka message
        segments_df = parse_compressed_data(compressed_segments)
        # Move column 'segment_id' in first position in the DataFrame
        cols = ['segment_id'] + [col for col in segments_df.columns if col != 'segment_id']
        segments_df = segments_df[cols]
        
        # Compute metrics for efficiency score
        segments_df = segments_df.apply(calculate_metrics, axis=1)

        # Add efficiency_score columng
        segments_df = compute_efficiency_score(segments_df, EFFICIENCY_FACTOR_SCALE, EFFICIENCY_ELEVATION_WEIGHT, EFFICIENCY_FACTOR_HR_DRIFT_WEIGHT)

        # Add user_id column
        segments_df['user_id'] = user_id

        # Store segments into database and update activity status
        segments_batch_insert_and_update_status(segments_df, activity_id, engine)
        logger.info(f"Stored {len(segments_df)} segments for activity {activity_id} into database")
    
    except DatabaseException as de:
        logger.error(f"An error occurred while storing segments for activity {activity_id}: {de}")
    except Exception as e:
        logger.error(e)

def compute_efficiency_score(df, s, k, m):
  """
  Computes Efficiency Score with the formula:
  Scaling factor * (Speed * (1 + Elevation Weight * |Elevation Change| / Distance)) / (Average Heart Rate (1 + m * (End Heart Rate - Start Heart Rate)))
  """  
  logger.info(f"Computing efficiency score with S={s}, k={k}, m={m}")
   
  df["efficiency_score"] = s * (df["avg_speed"] * (1 + k * abs(df["elevation_gain"]) / df["segment_length"])) / (df["avg_heartrate"] / 60 * (1 + m * df["hr_drift"]))
  return df

def calculate_metrics(segment):
    """Adds columns with metrics"""
    # Compute average speed
    segment["avg_speed"] = segment["segment_length"] / (segment["end_time"] - segment["start_time"])
    # Compute elevation gain
    segment["elevation_gain"] = segment["end_altitude"] - segment["start_altitude"]
    # Heartrate variation factor
    segment["hr_drift"] = (segment["end_heartrate"] - segment["start_heartrate"])/segment["start_heartrate"]
    return segment

def process_deleted_activities(user_id, deleted_activity_ids):
    try:
        delete_all_data_by_activity_ids(deleted_activity_ids)
        logger.info(f"Deleted all data for activity ids {deleted_activity_ids} of user {user_id}")
    except DatabaseException as e:
        logger.error(f"Unable to delete data for activity ids {deleted_activity_ids}: {e}")