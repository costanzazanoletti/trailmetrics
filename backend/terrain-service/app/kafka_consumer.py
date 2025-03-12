import json
import os
import base64
import logging
import logging_setup
from kafka import KafkaConsumer
from dotenv import load_dotenv
from app.terrain_service import get_terrain_info

# Load environment variables
load_dotenv()

# Kafka Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP")
KAFKA_TOPIC_INPUT = os.getenv("KAFKA_TOPIC_INPUT")
if not all([KAFKA_BROKER, KAFKA_CONSUMER_GROUP, KAFKA_TOPIC_INPUT]):
    raise ValueError("Kafka environment variables are not set properly")


# Setup logging
logger = logging.getLogger("app")
logger.info(f"Using Kafka broker: {KAFKA_BROKER}")

def create_kafka_consumer():
    """Creates and returns a Kafka consumer instance."""
    return KafkaConsumer(
        KAFKA_TOPIC_INPUT,
        bootstrap_servers=KAFKA_BROKER,
        group_id=KAFKA_CONSUMER_GROUP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        auto_offset_reset="earliest",
        enable_auto_commit=True
    )

def process_message(message):
    """Processes a single Kafka message."""

    try:
        data = message.value if isinstance(message.value, dict) else json.loads(message.value)


        activity_id = data.get("activityId")
        processed_at = data.get("processedAt")
        compressed_segments = data.get("compressedSegments")

        if not activity_id or not compressed_segments:
            logger.warning("Received message without valid 'activityId' or payload, ignoring...")
            return
        
        # Decode the base64 value if it's a string
        if isinstance(compressed_segments, str):
            compressed_segments = base64.b64decode(compressed_segments)

        logger.info(f"Processing terrain info for Activity ID: {activity_id}, processed at: {processed_at}")

        # Fetch terrain info
        terrain_df = get_terrain_info(activity_id, compressed_segments)
        logger.info(terrain_df.head())

    except Exception as e:
        logger.error(f"Error processing message: {e}")


def start_kafka_consumer():
    """Starts the Kafka consumer and processes messages."""
    consumer = create_kafka_consumer()
    logger.info(f"Kafka Consumer is listening on topic '{KAFKA_TOPIC_INPUT}'...")
    try:
        for message in consumer:
            process_message(message)
    except KeyboardInterrupt:
        logger.info("Shutting down Kafka consumer...")
    finally:
        consumer.close()