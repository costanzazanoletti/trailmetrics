import json
import os
import base64
import logging
import logging_setup
import pandas as pd
from kafka import KafkaConsumer
from dotenv import load_dotenv
from app.segmentation_service import segment_activity, segment_planned_activity
from app.kafka_producer import send_segmentation_output

# Setup logging
logger = logging.getLogger("app")
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
        if isinstance(message.value, bytes):
            data = json.loads(message.value.decode("utf-8")) 
        else:
            data = message.value  

        activity_id = data.get("activityId")
        is_planned = data.get("isPlanned")
        duration = data.get("duration")
        user_id = data.get("userId")
        start_date = data.get("startDate")
        processed_at = data.get("processedAt")
        compressed_stream = data.get("compressedStream")

        if not activity_id:
            logger.warning("Received message without valid 'activityId', ignoring...")
            return
        if not compressed_stream:
            logger.warning("Received message without compressed stream")
             # Produce Kafka message of segmentation output failure
            send_segmentation_output(activity_id, user_id, pd.DataFrame(), processed_at, start_date, 'failure', is_planned, duration)
            return
        
        # Decode the base64 value if it's a string
        if isinstance(compressed_stream, str):
            compressed_stream = base64.b64decode(compressed_stream)
        
        # Check if it's a planned or historical activity
        segments_df = pd.DataFrame()    
        if is_planned:
            logger.info(f"Processing segmentation for Planned Activity ID: {activity_id}, processed at: {processed_at}")
            # Perform segmentation
            segments_df = segment_planned_activity(activity_id, compressed_stream, duration)
        else:    
            logger.info(f"Processing segmentation for Activity ID: {activity_id}, processed at: {processed_at}")
            # Perform segmentation
            segments_df = segment_activity(activity_id, compressed_stream)

        if not segments_df.empty:
            segment_count = len(segments_df)
            logger.info(f"Segmentation completed for Activity ID: {activity_id}, {segment_count} segments created.")
            
            # Produce Kafka message of segmentation output success
            send_segmentation_output(activity_id, user_id, segments_df, processed_at, start_date, 'success', is_planned, duration)
        else:
            logger.warning(f"Empty segments for Activity ID: {activity_id}")
             # Produce Kafka message of segmentation output failure
            send_segmentation_output(activity_id, user_id, segments_df, processed_at, start_date, 'failure', is_planned, duration)
    
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