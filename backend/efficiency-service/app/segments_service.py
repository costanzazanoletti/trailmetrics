import logging
import logging_setup
import json
import gzip
import pandas as pd
import numpy as np
from app.exceptions import DatabaseException
from database import segments_batch_insert_and_update_status
from app.utilities import parse_compressed_data

logger = logging.getLogger("app")

def process_segments(activity_id, compressed_segments):
    """Processes segments"""
    try:
        # Extract segments DataFrame from Kafka message
        segments_df = parse_compressed_data(compressed_segments)
        
        # Store segments into database and update activity status
        segments_batch_insert_and_update_status(segments_df, activity_id)
        logger.info(f"Stored {len(segments_df)} segments for Activity ID {activity_id} into database")
    
    except DatabaseException as de:
        logger.error(f"An error occurred while storing segments for Activity ID {activity_id}: {de}")
    except Exception as e:
        logger.error(e)