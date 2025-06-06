import json
import os
import base64
import logging
import logging_setup
import time
from datetime import datetime, timezone
from kafka import KafkaConsumer
from dotenv import load_dotenv
from app.weather.weather_pipeline import (
    get_weather_info, 
    get_weather_data_from_api
    )

# Load environment variables
load_dotenv()


# Kafka Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP")
KAFKA_TOPIC_INPUT = os.getenv("KAFKA_TOPIC_INPUT")
KAFKA_MAX_POLL_RECORDS = int(os.getenv("KAFKA_MAX_POLL_RECORDS", 10))
KAFKA_MAX_POLL_INTERVAL_MS = int(os.getenv("KAFKA_MAX_POLL_INTERVAL_MS", 600000)) 
KAFKA_SESSION_TIMEOUT_MS = int(os.getenv("KAFKA_SESSION_TIMEOUT_MS", 40000))
KAFKA_HEARTBEAT_INTERVAL_MS = int(os.getenv("KAFKA_HEARTBEAT_INTERVAL_MS", 10000)) 

# Kafka Retry Configuration
KAFKA_RETRY_CONSUMER_GROUP = os.getenv("KAFKA_RETRY_CONSUMER_GROUP")
KAFKA_RETRY_TOPIC_INPUT = os.getenv("KAFKA_RETRY_TOPIC_INPUT")
KAFKA_RETRY_MAX_POLL_RECORDS = int(os.getenv("KAFKA_RETRY_MAX_POLL_RECORDS", 100))
KAFKA_RETRY_MAX_POLL_INTERVAL_MS = int(os.getenv("KAFKA_RETRY_MAX_POLL_INTERVAL_MS", 3600000)) 
KAFKA_RETRY_SESSION_TIMEOUT_MS = int(os.getenv("KAFKA_RETRY_SESSION_TIMEOUT_MS", 60000))
KAFKA_RETRY_HEARTBEAT_INTERVAL_MS = int(os.getenv("KAFKA_RETRY_HEARTBEAT_INTERVAL_MS", 20000)) 

if not all([KAFKA_BROKER, KAFKA_CONSUMER_GROUP, KAFKA_TOPIC_INPUT,KAFKA_MAX_POLL_RECORDS]):
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
        enable_auto_commit=False,
        max_poll_records=KAFKA_MAX_POLL_RECORDS,
        max_poll_interval_ms=KAFKA_MAX_POLL_INTERVAL_MS,
        session_timeout_ms=KAFKA_SESSION_TIMEOUT_MS,
        heartbeat_interval_ms=KAFKA_HEARTBEAT_INTERVAL_MS,
    )

def create_kafka_retry_consumer():
    """Creates and returns a Kafka consumer instance."""
    return KafkaConsumer(
        KAFKA_RETRY_TOPIC_INPUT,
        bootstrap_servers=KAFKA_BROKER,
        group_id=KAFKA_RETRY_CONSUMER_GROUP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        max_poll_records=KAFKA_RETRY_MAX_POLL_RECORDS,
        max_poll_interval_ms=KAFKA_RETRY_MAX_POLL_INTERVAL_MS,
        session_timeout_ms=KAFKA_RETRY_SESSION_TIMEOUT_MS,
        heartbeat_interval_ms=KAFKA_RETRY_HEARTBEAT_INTERVAL_MS,
    )

def process_message(message):
    """Processes a single Kafka message."""
    try:
        data = message.value if isinstance(message.value, dict) else json.loads(message.value)

        activity_id = data.get("activityId")
        is_planned = data.get("isPlanned")
        duration = data.get("duration")
        start_date = data.get("startDate")
        status = data.get("status")
        compressed_segments = data.get("compressedSegments")

        if not activity_id or not compressed_segments or not start_date or not status or status == 'failure':
            logger.warning("Received message without valid 'activityId' or payload, ignoring...")
            return
        
        # Decode the base64 value if it's a string
        if isinstance(compressed_segments, str):
            compressed_segments = base64.b64decode(compressed_segments)

            logger.info(f"Processing weather info for{' planned' if is_planned else ''} Activity ID: {activity_id}")
            get_weather_info(start_date, duration, compressed_segments, activity_id, is_planned)

    except Exception as e:
        logger.error(f"Error processing message: {e}")

def process_retry_message(message):

    try:
        data = message.value if isinstance(message.value, dict) else json.loads(message.value)
        activity_id = data.get("activityId")
        request_params = data.get("requestParams")
        segment_ids = data.get("segmentIds")
        group_id = data.get("groupId")
        retry_timestamp = data.get("retryTimestamp")
        retries = data.get("retries")
        api_type = data.get("apiType")

        if not activity_id or not retry_timestamp:
            logger.warning("Received retry message without 'activityId' or 'retryTimestamp'")
            return
        
        # Current time to check the delay
        current_time = int(datetime.now(timezone.utc).timestamp())

        # If retry_timestamp is not yet arrived
        if current_time < retry_timestamp:
            delay = retry_timestamp - current_time
            logger.info(f"Message for activity ID {activity_id} group {group_id} rescheduled. Waiting {delay} seconds before retry.")
            time.sleep(delay)
      
        logger.info(f"Retry time reached for activity ID {activity_id} group {group_id}. Processing message.")
        # Process the retry message
        get_weather_data_from_api(api_type, activity_id, segment_ids, request_params, group_id, retries)

    except Exception as e:
        logger.error(f"Error processing retry message {e}")

def start_kafka_consumer(shutdown_event):
    """Starts the Kafka consumer and processes messages."""
    consumer = create_kafka_consumer()
    logger.info(f"Kafka Consumer is listening on topic '{KAFKA_TOPIC_INPUT}'...")
    try:
        while not shutdown_event.is_set():
            for message in consumer:
                process_message(message)
                consumer.commit()

        logger.info("Shutting down Kafka consumer...")
    finally:
        consumer.close()

def start_kafka_retry_consumer(shutdown_event):
    """Starts the Kafka consumer for retry messages and processes retry messages."""
    consumer = create_kafka_retry_consumer()
    logger.info(f"Kafka Retry Consumer is listening on topic '{KAFKA_RETRY_TOPIC_INPUT}'...")

    try:
        while not shutdown_event.is_set():
            for message in consumer:
                process_retry_message(message) 
                consumer.commit()
                              
        logger.info("Shutting down Kafka retry consumer...")
    finally:
        consumer.close()