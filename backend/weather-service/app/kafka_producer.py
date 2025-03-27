import json
import os
import base64
import gzip
import logging
import logging_setup
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
