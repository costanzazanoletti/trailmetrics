import logging
import logging_setup
import pandas as pd
import numpy as np
from app.exceptions import DatabaseException
from app.utilities import parse_compressed_data
from database import weather_batch_insert_and_update_status

logger = logging.getLogger("app")

def process_weather_info(activity_id, group_id, compressed_weather_info, engine):
    """Processes weather info"""
    try:
        weather_df = parse_compressed_data(compressed_weather_info)
        
        # Keep only columns that are actually stored
        columns_to_keep = ['segment_id','temp', 'feels_like', 'humidity', 'wind', 'weather_id', 'weather_main', 'weather_description']
        weather_df = weather_df[columns_to_keep]

        # Add 'activity_id' column
        weather_df['activity_id'] = weather_df['segment_id'].str.split('-').str[0].astype(int)
        
        # Get number of groups
        total_groups = int(group_id.split("_")[1])
        
        # Store segments into database and update activity status
        weather_batch_insert_and_update_status(weather_df, activity_id, group_id, total_groups, engine)
        logger.info(f"Stored {len(weather_df)} segment weather info for activity {activity_id}, group {group_id} into database")
    
    except DatabaseException as de:
        logger.error(f"An error occurred while storing segment weather info for activity {activity_id}: {de}")
    except Exception as e:
        logger.error(e)