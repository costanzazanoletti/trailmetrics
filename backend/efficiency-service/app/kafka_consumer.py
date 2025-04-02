import json
import os
import base64
import logging
import logging_setup
import time
from kafka import KafkaConsumer
from dotenv import load_dotenv
from app.segments_service import process_segments
from app.terrain_service import process_terrain_info
from app.weather_service import process_weather_info


# Load environment variables
load_dotenv()

# Kafka Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP")
KAFKA_TOPIC_SEGMENTS = os.getenv("KAFKA_TOPIC_SEGMENTS")
KAFKA_TOPIC_TERRAIN = os.getenv("KAFKA_TOPIC_TERRAIN")
KAFKA_TOPIC_WEATHER = os.getenv("KAFKA_TOPIC_WEATHER")

if not all([KAFKA_BROKER, KAFKA_CONSUMER_GROUP, KAFKA_TOPIC_SEGMENTS,KAFKA_TOPIC_TERRAIN,KAFKA_TOPIC_WEATHER]):
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
        compressed_segments = data.get("compressedSegments")

        if not activity_id or not compressed_segments:
            logger.warning("Received segments message without valid 'activityId' or 'compressedSegments'")
            return
            
        logger.info(f"Processing segments for activity {activity_id}")
        process_segments(activity_id, compressed_segments)

    except Exception as e:
        logger.error(f"Error processing segments message: {e}")

def process_terrain_message(message):
    """Processes a single Kafka terrain output message."""
    try:
        data = message.value if isinstance(message.value, dict) else json.loads(message.value)
        activity_id = data.get("activityId")
        compressed_terrain_info = data.get("compressedTerrainInfo")

        if not activity_id or not compressed_terrain_info:
            logger.warning("Received terrain message without valid 'activityId' or 'compressedTerrainInfo")
            return

        logger.info(f"Processing terrain info for activity {activity_id}")
        process_terrain_info(activity_id, compressed_terrain_info)

    except Exception as e:
        logger.error(f"Error processing terrain message: {e}")

def process_weather_message(message):
    """Processes a single Kafka weather output message."""
    try:
        data = message.value if isinstance(message.value, dict) else json.loads(message.value)
        activity_id = data.get("activityId")
        group_id = data.get("groupId")
        compressed_weather_info = data.get("compressedWeatherInfo")

        if not activity_id or not group_id or not compressed_weather_info:
            logger.warning("Received weather message without valid 'activityId' or 'groupId' or 'compressedWeatherInfo'")
            return

        logger.info(f"Processing weather info for activity {activity_id}")
        process_weather_info(activity_id, group_id, compressed_weather_info)

    except Exception as e:
        logger.error(f"Error processing weather message: {e}")

def start_kafka_segments_consumer(shutdown_event):
    """Starts the Kafka consumer for segmentation output."""
    consumer = create_kafka_consumer(KAFKA_TOPIC_SEGMENTS)
    logger.info(f"Kafka Retry Consumer is listening on topic '{KAFKA_TOPIC_SEGMENTS}'...")
    try:
        while not shutdown_event.is_set():
            for message in consumer:
                process_segments_message(message)
                #consumer.commit()
        logger.info("Shutting down Kafka segments consumer...")
    finally:
        consumer.close()

def start_kafka_terrain_consumer(shutdown_event):
    """Starts the Kafka consumer for terrain output."""
    consumer = create_kafka_consumer(KAFKA_TOPIC_TERRAIN)
    logger.info(f"Kafka Retry Consumer is listening on topic '{KAFKA_TOPIC_TERRAIN}'...")
    try:
        while not shutdown_event.is_set():
            for message in consumer:
                process_terrain_message(message)
                #consumer.commit()
        logger.info("Shutting down Kafka terrain consumer...")
    finally:
        consumer.close()

def start_kafka_weather_consumer(shutdown_event):
    """Starts the Kafka consumer for terrain output."""
    consumer = create_kafka_consumer(KAFKA_TOPIC_WEATHER)
    logger.info(f"Kafka Retry Consumer is listening on topic '{KAFKA_TOPIC_WEATHER}'...")
    try:
        while not shutdown_event.is_set():
            for message in consumer:
                process_weather_message(message)
                #consumer.commit()
        logger.info("Shutting down Kafka weather consumer...")
    finally:
        consumer.close()