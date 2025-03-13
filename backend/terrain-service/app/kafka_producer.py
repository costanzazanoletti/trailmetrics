import json
import os
import base64
import gzip
import logging
import logging_setup
from dotenv import load_dotenv
from kafka import KafkaProducer

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger("terrain")

# Kafka Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_TOPIC_OUTPUT = os.getenv("KAFKA_TOPIC_OUTPUT")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: str(k).encode("utf-8")
)


def prepare_terrain_message(activity_id, segments_df, processed_at):
    """Prepare the output message with compressed terrain info"""
    
    # Keep only required columns
    segments = segments_df[["segmentId", "highway", "surface"]].to_dict(orient="records")

    # Convert segments in json and compress
    json_segments = json.dumps(segments).encode("utf-8")
    compressed_segments = gzip.compress(json_segments)
    encoded_segments = base64.b64encode(compressed_segments).decode("utf-8")

    # Return message
    return {
        "activityId": activity_id,
        "processedAt": processed_at,
        "compressedTerrainInfo": encoded_segments
    }

def send_terrain_output(activity_id, terrain_df, processed_at):
    """Send terrain output message to Kafka."""
    
    # Prepare message with compressed segments
    kafka_message = prepare_terrain_message(activity_id, terrain_df, processed_at)

    # Send message to Kafka
    producer.send(KAFKA_TOPIC_OUTPUT, key=str(activity_id), value=kafka_message)

    logger.info(f"Sent terrain info Kafka message for Activity ID: {activity_id}: {len(terrain_df)} segments, "
            f"{terrain_df['highway'].isna().sum()} missing highway, "
            f"{terrain_df['surface'].isna().sum()} missing surface")
