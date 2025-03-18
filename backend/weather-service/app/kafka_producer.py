import json
import os
import base64
import gzip
import logging
import logging_setup
from dotenv import load_dotenv
from kafka import KafkaProducer
from app.weather_api_service import generate_variables_mapping

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

    # Get the weather column mapping from generate_variables_mapping
    weather_mapping, _ = generate_variables_mapping()

    # Keep only required columns: 'segmentId' + weather columns from weather_mapping
    required_columns = ["segmentId"] + list(weather_mapping.values())
    
    # Filter the DataFrame to keep only the necessary columns
    segments = segments_df[required_columns].to_dict(orient="records")

    # Convert segments in json and compress
    json_segments = json.dumps(segments).encode("utf-8")
    compressed_segments = gzip.compress(json_segments)
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
