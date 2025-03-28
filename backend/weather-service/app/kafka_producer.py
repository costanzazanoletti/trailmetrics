import json
import os
import base64
import gzip
import logging
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
KAFKA_TOPIC_RETRY = os.getenv("KAFKA_TOPIC_RETRY")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: str(k).encode("utf-8")
)


def prepare_message(activity_id, segments_df, processed_at):
    """Prepare the output message with compressed weather info"""
    # Convert the DataFrame to a list of dictionaries 
    json_segments = segments_df.to_dict(orient="records") 

    # Convert the list of dictionaries to JSON string and then compress it
    json_segments_str = json.dumps(json_segments).encode("utf-8")
    compressed_segments = gzip.compress(json_segments_str)
    
    # Encode the compressed data to base64
    encoded_segments = base64.b64encode(compressed_segments).decode("utf-8")
    
    # Return message
    return {
        "activityId": activity_id,
        "processedAt": processed_at,
        "compressedWeatherInfo": encoded_segments
    }

def send_weather_output(activity_id, weather_df, processed_at):
    """Send terrain output message to Kafka."""
    
    # Prepare message with compressed segments
    kafka_message = prepare_message(activity_id, weather_df, processed_at)

    # Send message to Kafka
    producer.send(KAFKA_TOPIC_OUTPUT, key=str(activity_id), value=kafka_message)
    logger.info(f"Sent weather info Kafka message for Activity ID: {activity_id}: {len(weather_df)} segments")

def prepare_retry_message(activity_id, reference_point, request_params, short):
    """Prepare the retry message with the reference point and request params and the retry timestamp"""
    # Compute the retry time
    retry_time = datetime.now(timezone.utc)
    if short:
        # Add 1 hour if "short" is true
        retry_time = retry_time + timedelta(hours=1)
    else:
        retry_time = retry_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    retry_timestamp = int(retry_time.timestamp())

    # Convert the DataFrame to a list of dictionaries 
    json_rf = reference_point.to_dict(orient="records") 

    # Create the message with the retry timestamp
    return {
        "activityId": activity_id,
        "request_params": request_params,
        "reference_point": json_rf,
        "retry_timestamp": retry_timestamp
    }

def send_retry_message(activity_id, reference_point, request_params, short = False):
    retry_message = prepare_retry_message(activity_id, reference_point, request_params, short)
    logger.info(f"Retry Message: {retry_message}")
    #producer.send(KAFKA_TOPIC_RETRY, key=str(activity_id).encode('utf-8'), value=json.dumps(retry_message).encode('utf-8'))