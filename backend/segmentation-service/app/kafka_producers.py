import json
import os
import logging
from kafka import KafkaProducer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Kafka Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TERRAIN_TOPIC_OUTPUT = os.getenv("KAFKA_TERRAIN_TOPIC_OUTPUT", "activity-terrain-request-queue")
KAFKA_WEATHER_TOPIC_OUTPUT = os.getenv("KAFKA_WEATHER_TOPIC_OUTPUT", "activity-weather-request-queue")

logger = logging.getLogger("kafka_producers")

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    key_serializer=lambda k: k.encode("utf-8"),  # Ensure key is a string
    value_serializer=lambda m: json.dumps(m).encode("utf-8")
)

def send_terrain_request(activity_id, segmented_at):
    """
    Sends a Kafka message to request terrain data for an activity.
    """
    try:
        producer.send(
            KAFKA_TERRAIN_TOPIC_OUTPUT,
            key=activity_id,
            value={
                "activityId": activity_id,
                "requestedAt": segmented_at
            }
        )
        logger.info(f"Published terrain request for Activity ID: {activity_id}")
    except Exception as e:
        logger.error(f"Error publishing terrain request for {activity_id}: {e}")

def send_weather_request(activity_id, segmented_at):
    """
    Sends a Kafka message to request weather data for an activity.
    """
    try:
        producer.send(
            KAFKA_WEATHER_TOPIC_OUTPUT,
            key=activity_id,
            value={
                "activityId": activity_id,
                "requestedAt": segmented_at
            }
        )
        logger.info(f"Published weather request for Activity ID: {activity_id}")
    except Exception as e:
        logger.error(f"Error publishing weather request for {activity_id}: {e}")
