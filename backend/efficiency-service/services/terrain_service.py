import logging
import logging_setup
from exceptions.exceptions import DatabaseException
from utils.compression import parse_compressed_data
from db.segments import terrain_batch_insert_and_update_status

logger = logging.getLogger("app")


def process_terrain_info(activity_id, compressed_terrain_info, engine):
    """Processes segments"""
    try:
        # Extract segments DataFrame from Kafka message
        terrain_df = parse_compressed_data(compressed_terrain_info)
        # Add 'activity_id' column
        terrain_df['activity_id'] = terrain_df['segment_id'].str.split('-').str[0].astype(int)
        # Store segments into database and update activity status
        terrain_batch_insert_and_update_status(terrain_df, activity_id, engine)
        logger.info(f"Stored {len(terrain_df)} segment terrain info for activity {activity_id} into database")
    
    except DatabaseException as de:
        logger.error(f"An error occurred while storing segment terrain info for activity {activity_id}: {de}")
    except Exception as e:
        logger.error(e)