import json
import os
import logging
import logging_setup
from kafka import KafkaConsumer
from dotenv import load_dotenv
from app.process_messages import (
    process_segments_message,
    process_deleted_activities_message,
    process_terrain_message,
    process_weather_message
    )

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