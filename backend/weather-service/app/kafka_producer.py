import json
import os
import base64
import gzip
import logging
import pandas as pd
import logging_setup
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from kafka import KafkaProducer
from app.openweather_api_service import generate_weather_variables_mapping

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger("app")

# Kafka Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_TOPIC_OUTPUT = os.getenv("KAFKA_TOPIC_OUTPUT")
KAFKA_TOPIC_RETRY = os.getenv("KAFKA_RETRY_TOPIC_INPUT")
KAFKA_RETRY_MAX_POLL_INTERVAL_MS = os.getenv("KAFKA_RETRY_MAX_POLL_INTERVAL_MS")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: str(k).encode("utf-8"),
    request_timeout_ms=30000
)

def dataframe_to_compressed_json(df):
    # Convert the DataFrame to a list of dictionaries 
    json_data = df.to_dict(orient="records") 
    # Convert the list of dictionaries to JSON string and then compress it
    json_str = json.dumps(json_data).encode("utf-8")
    compressed_json = gzip.compress(json_str)
    # Encode the compressed data to base64
    return base64.b64encode(compressed_json).decode("utf-8")

def prepare_message(activity_id, segments_df, reference_point_id):
    """Prepare the output message with compressed weather info"""
    # Prepare the compressed segments
    encoded_segments = dataframe_to_compressed_json(segments_df) 
    # Return message
    return {
        "activityId": activity_id,
        "groupId": reference_point_id,
        "compressedWeatherInfo": encoded_segments
    }

def send_weather_output(activity_id, weather_df, reference_point_id):
    """Send weather output message to Kafka."""
    # Prepare message with compressed segments
    kafka_message = prepare_message(activity_id, weather_df, reference_point_id)

    # Send message to Kafka
    try:
        producer.send(KAFKA_TOPIC_OUTPUT, key=activity_id, value=kafka_message)
        producer.flush()  
        logger.info(f"Sent weather info Kafka message for Activity ID: {activity_id} group {reference_point_id}: {len(weather_df)} segments")
    except Exception as e:
        logger.error(f"Error sending weather info for Activity ID {activity_id}: {e} group {reference_point_id}")

def send_retry_message(activity_id, segment_ids, group_id, request_params, retries):
    """Prepare the retry message with the reference point and request params and the retry timestamp"""
    # Compute the retry time based on Kafka max poll interval
    retry_time_seconds = int(KAFKA_RETRY_MAX_POLL_INTERVAL_MS)/1000 - 1
    retry_time = datetime.now(timezone.utc) + timedelta(seconds=retry_time_seconds)  
    retry_timestamp = int(retry_time.timestamp())
    retries = retries + 1
    
    # Create the message with the retry timestamp
    retry_message = {
        "activityId": activity_id,
        "requestParams": request_params,
        "segmentIds": segment_ids,
        "groupId": group_id,
        "retryTimestamp": retry_timestamp,
        "retries" : retries
    }

    # Send the message to Kafka
    try:
        producer.send(KAFKA_TOPIC_RETRY, key=activity_id, value=retry_message)
        producer.flush()  
        logger.info(f"Sent retry message {retries} for Activity ID {activity_id} group {group_id} retry in {retry_time_seconds} seconds")
    except Exception as e:
        logger.error(f"Error sending retry message for Activity ID {activity_id} group {group_id}: {e}")

    