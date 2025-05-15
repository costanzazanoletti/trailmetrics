import logging
import logging_setup
import json
from services.segments_service import process_segments, process_deleted_activities
from services.terrain_service import process_terrain_info
from services.weather_service import process_weather_info
from services.similarity_service import should_compute_similarity_for_user
from db.setup import engine
from db.activities import get_user_id_from_activity, insert_not_processable_activity_status

# Setup logging
logger = logging.getLogger("app")

def process_segments_message(message):
    """Processes a single Kafka segmentation output message."""
    try:
        data = message.value if isinstance(message.value, dict) else json.loads(message.value)
        activity_id = data.get("activityId")
        user_id = str(data.get("userId"))
        status = data.get("status")
        compressed_segments = data.get("compressedSegments")

        # Check if the message is valid
        if not activity_id:
            logger.warning("Received segments message without valid 'activityId', ignoring...'")
            return
        
        # Check if the activity is not processable
        if not compressed_segments or not status or status == 'failure':
            logger.info(f"Received not processable activity {activity_id}")
            # Insert into activity status tracker the activity with not_processable 
            insert_not_processable_activity_status(activity_id, engine)
            logger.info(f"Saved activity status not processable for activity {activity_id}")
        else:
            # Process segments
            logger.info(f"Processing segments for activity {activity_id}")
            process_segments(activity_id, user_id, compressed_segments, engine)
        
        # Check if similarity matrix should be computed
        should_compute_similarity_for_user(engine, str(user_id))

    except Exception as e:
        logger.error(f"Error processing segments message: {e}")

def process_terrain_message(message):
    """Processes a single Kafka terrain output message."""
    try:
        data = message.value if isinstance(message.value, dict) else json.loads(message.value)
        activity_id = data.get("activityId")
        user_id = str(data.get("userId"))
        compressed_terrain_info = data.get("compressedTerrainInfo")

        if not activity_id or not compressed_terrain_info:
            logger.warning("Received terrain message without valid 'activityId' or 'compressedTerrainInfo")
            return

        logger.info(f"Processing terrain info for activity {activity_id}")
        process_terrain_info(activity_id, compressed_terrain_info, engine)
        # Check if similarity matrix should be computed
        should_compute_similarity_for_user(engine, user_id)

    except Exception as e:
        logger.error(f"Error processing terrain message: {e}")

def process_weather_message(message):
    """Processes a single Kafka weather output message."""
    try:
        data = message.value if isinstance(message.value, dict) else json.loads(message.value)
        activity_id = data.get("activityId")
        user_id = get_user_id_from_activity(engine, activity_id)
        group_id = data.get("groupId")
        compressed_weather_info = data.get("compressedWeatherInfo")

        if not activity_id or not group_id or not compressed_weather_info:
            logger.warning("Received weather message without valid 'activityId' or 'groupId' or 'compressedWeatherInfo'")
            return

        logger.info(f"Processing weather info for activity {activity_id}")
        process_weather_info(activity_id, group_id, compressed_weather_info, engine)
        # Check if similarity matrix should be computed
        should_compute_similarity_for_user(engine, user_id)
    except Exception as e:
        logger.error(f"Error processing weather message: {e}")

def process_deleted_activities_message(message):
    """Processes a single Kafka message with deleted activity ids."""
    try:
        data = message.value if isinstance(message.value, dict) else json.loads(message.value)
        user_id = data.get("userId")
        checked_at = data.get("checkedAt")
        deleted_activity_ids = data.get("deletedActivityIds")
  
        if not user_id or not deleted_activity_ids:
            logger.warning("Received user activities changes message without valid 'userId' or deleted activity ids")
            return
            
        logger.info(f"Processing {len(deleted_activity_ids)} deleted activities for user {user_id}")
        process_deleted_activities(user_id, deleted_activity_ids)
        # Check if similarity matrix should be computed
        should_compute_similarity_for_user(engine, user_id)

    except Exception as e:
        logger.error(f"Error processing deleted activities message: {e}")
