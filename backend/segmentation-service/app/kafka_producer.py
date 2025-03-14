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

def prepare_segmentation_message(activity_id, segments_df, processed_at, start_date):
    """Prepare the output message with compressed segments"""
    segments = []
    
    for idx, row in segments_df.iterrows():
        segment = {
            "segmentId": f"{activity_id}-{idx+1}",  # create unique ID for each segment
            "start_distance": row["start_distance"],
            "end_distance": row["end_distance"],
            "segment_length": row["segment_length"],
            "avg_gradient": row["avg_gradient"],
            "avg_cadence": row["avg_cadence"],
            "type": row["type"],
            "grade_category": row["grade_category"],
            "start_lat": row["start_lat"],
            "start_lng": row["start_lng"],
            "end_lat": row["end_lat"],
            "end_lng": row["end_lng"]
        }
        segments.append(segment)

    # Convert segments in json and compress
    json_segments = json.dumps(segments).encode("utf-8")
    compressed_segments = gzip.compress(json_segments)
    encoded_segments = base64.b64encode(compressed_segments).decode("utf-8")

    # Return message
    return {
        "activityId": activity_id,
        "startDate": start_date,
        "processedAt": processed_at,
        "compressedSegments": encoded_segments
    }

def send_segmentation_output(activity_id, segments_df, processed_at, start_date):
    """Send segmentation output message to Kafka."""
    
    # Prepare message with compressed segments
    kafka_message = prepare_segmentation_message(activity_id, segments_df, processed_at, start_date)

    # Send message to Kafka
    producer.send(KAFKA_TOPIC_OUTPUT, key=str(activity_id), value=kafka_message)

    print(f"Sent segmentation message for activity {activity_id} with {len(segments_df)} segments.")
    logger.info(f"Sent segmentation message for activity {activity_id} with {len(segments_df)} segments.")
