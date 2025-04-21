import json
import os
import base64
import logging
import logging_setup
import time
from kafka import KafkaConsumer
from dotenv import load_dotenv
from app.segments_service import process_segments, process_deleted_activities
from app.terrain_service import process_terrain_info
from app.weather_service import process_weather_info
from app.similarity_service import should_compute_similarity_for_user
from database import engine, get_user_id_from_activity, insert_not_processable_actitivity_status


# Load environment variables
load_dotenv()

# Kafka Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP")
KAFKA_TOPIC_SEGMENTS = os.getenv("KAFKA_TOPIC_SEGMENTS")
KAFKA_TOPIC_TERRAIN = os.getenv("KAFKA_TOPIC_TERRAIN")
KAFKA_TOPIC_WEATHER = os.getenv("KAFKA_TOPIC_WEATHER")
KAFKA_TOPIC_DELETED_ACTIVITIES = os.getenv("KAFKA_TOPIC_DELETED_ACTIVITIES")

if not all([KAFKA_BROKER, KAFKA_CONSUMER_GROUP, KAFKA_TOPIC_SEGMENTS,KAFKA_TOPIC_TERRAIN,KAFKA_TOPIC_WEATHER, KAFKA_TOPIC_DELETED_ACTIVITIES]):
    raise ValueError("Kafka environment variables are not set properly")


# Setup logging
logger = logging.getLogger("app")
logger.info(f"Using Kafka broker: {KAFKA_BROKER}")

def create_kafka_consumer(topic):
    """Creates and returns a Kafka consumer instance."""
    return KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BROKER,
        group_id=KAFKA_CONSUMER_GROUP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        auto_offset_reset="earliest",
    )

def process_segments_message(message):
    """Processes a single Kafka segmentation output message."""
    try:
        data = message.value if isinstance(message.value, dict) else json.loads(message.value)
        activity_id = data.get("activityId")
        user_id = data.get("userId")
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
            insert_not_processable_actitivity_status(activity_id, engine)
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
        user_id = data.get("userId")
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

def start_kafka_segments_consumer(shutdown_event):
    """Starts the Kafka consumer for segmentation output."""
    consumer = create_kafka_consumer(KAFKA_TOPIC_SEGMENTS)
    logger.info(f"Kafka Consumer is listening on topic '{KAFKA_TOPIC_SEGMENTS}'...")
    try:
        while not shutdown_event.is_set():
            for message in consumer:
                process_segments_message(message)
                consumer.commit()
        logger.info("Shutting down Kafka segments consumer...")
    finally:
        consumer.close()

def start_kafka_terrain_consumer(shutdown_event):
    """Starts the Kafka consumer for terrain output."""
    consumer = create_kafka_consumer(KAFKA_TOPIC_TERRAIN)
    logger.info(f"Kafka Consumer is listening on topic '{KAFKA_TOPIC_TERRAIN}'...")
    try:
        while not shutdown_event.is_set():
            for message in consumer:
                process_terrain_message(message)
                consumer.commit()
        logger.info("Shutting down Kafka terrain consumer...")
    finally:
        consumer.close()

def start_kafka_weather_consumer(shutdown_event):
    """Starts the Kafka consumer for terrain output."""
    consumer = create_kafka_consumer(KAFKA_TOPIC_WEATHER)
    logger.info(f"Kafka Consumer is listening on topic '{KAFKA_TOPIC_WEATHER}'...")
    try:
        while not shutdown_event.is_set():
            for message in consumer:
                process_weather_message(message)
                consumer.commit()
        logger.info("Shutting down Kafka weather consumer...")
    finally:
        consumer.close()

def start_kafka_deleted_activities_consumer(shutdown_event):
    """Starts the Kafka consumer for deleted activities."""
    consumer = create_kafka_consumer(KAFKA_TOPIC_DELETED_ACTIVITIES)
    logger.info(f"Kafka Consumer is listening on topic '{KAFKA_TOPIC_DELETED_ACTIVITIES}'...")
    try:
        while not shutdown_event.is_set():
            for message in consumer:
                process_deleted_activities_message(message)
                consumer.commit()
        logger.info("Shutting down Kafka changes consumer...")
    finally:
        consumer.close()