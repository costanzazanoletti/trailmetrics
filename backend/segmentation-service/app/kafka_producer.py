import json
import os
import base64
import gzip
import logging
from dotenv import load_dotenv
from kafka import KafkaProducer

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

def prepare_segmentation_message(activity_id, segments_df):
    """Prepare the output message with compressed segments"""
    # Assign a progressive id to each segment, left padded up to 5 digits
    segments_df = segments_df.assign(
        segment_id=segments_df.index.to_series().add(1).astype(str).str.zfill(5).radd(f"{activity_id}-")
    )

    # Convert the dataframe into a dictionary of lists of dictionaries
    segments = segments_df.to_dict(orient="records")

    # Convert segments in json and compress
    json_segments = json.dumps(segments).encode("utf-8")
    compressed_segments = gzip.compress(json_segments)
    encoded_segments = base64.b64encode(compressed_segments).decode("utf-8")
    
    return encoded_segments
    
def send_segmentation_output(activity_id, user_id, segments_df, processed_at, start_date, status, is_planned, duration):
    """Send segmentation output message to Kafka."""
    # Prepare message with compressed segments
    encoded_segments = prepare_segmentation_message(activity_id, segments_df)
    kafka_message = {
        "activityId": activity_id,
        "isPlanned": is_planned,
        "duration": duration,
        "userId": user_id,
        "startDate": start_date,
        "processedAt": processed_at,
        "status": status,
        "compressedSegments": encoded_segments
    }
    # Send message to Kafka
    producer.send(KAFKA_TOPIC_OUTPUT, key=str(activity_id), value=kafka_message)

    logger.info(f"Sent segmentation message for activity {activity_id} with {len(segments_df)} segments.")
