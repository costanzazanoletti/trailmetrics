import json
import os
from kafka import KafkaConsumer, KafkaProducer
from dotenv import load_dotenv
import logging
from app.segmentation import segment_activity

# Load environment variables
load_dotenv()

# Kafka Configuration
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "segmentation-service-group")
KAFKA_TOPIC_INPUT = os.getenv("KAFKA_TOPIC_INPUT", "activity-processed-queue")
KAFKA_TOPIC_OUTPUT = os.getenv("KAFKA_TOPIC_OUTPUT", "activity-segmented-queue")

logger = logging.getLogger("segmentation")

print(f"Using Kafka broker: {KAFKA_BROKER}")

def start_kafka_consumer():
    """
    Starts the Kafka consumer to listen for 'activity-processed-queue' messages
    and publishes results to 'activity-segmented-queue'.
    """
    consumer = KafkaConsumer(
        KAFKA_TOPIC_INPUT,
        bootstrap_servers=KAFKA_BROKER,
        group_id=KAFKA_CONSUMER_GROUP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,  # Ensure string keys
        auto_offset_reset="earliest",
        enable_auto_commit=True
    )

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        key_serializer=lambda k: k.encode("utf-8"),  # Ensure key is a string
        value_serializer=lambda m: json.dumps(m).encode("utf-8")
    )

    print(f"Kafka Consumer is listening for messages on '{KAFKA_TOPIC_INPUT}'...")

    for message in consumer:
        try:
            activity_id = message.key
            processed_at = message.value.get("processedAt")

            if not activity_id:
                print("Received message without 'activityId' key, ignoring...")
                continue

            print(f"Processing segmentation for Activity ID: {activity_id}, processed at: {processed_at}")
            logger.info(f"Processing segmentation for Activity ID: {activity_id}, processed at: {processed_at}")
            
            # Perform segmentation
            segments_df = segment_activity(activity_id)

            if not segments_df.empty:
                segment_count = len(segments_df)
                print(f"Segmentation completed for Activity ID: {activity_id}, {segment_count} segments created.")
                logger.info(f"Segmentation completed for Activity ID: {activity_id}, {segment_count} segments created.")

                try:
                    producer.send(
                        KAFKA_TOPIC_OUTPUT,
                        key=activity_id,
                        value={
                            "activityId": activity_id,
                            "segmentedAt": processed_at,
                            "segmentCount": segment_count
                        }
                    )
                    print(f"Published '{KAFKA_TOPIC_OUTPUT}' event for Activity ID: {activity_id}")
                except Exception as e:
                    print(f"Error publishing Kafka event for {activity_id}: {e}")
                    logger.info(f"Error publishing Kafka event for {activity_id}: {e}")
            else:
                print(f"Empty segments for Activity ID: {activity_id}")
                logger.warning(f"Empty segments for Activity ID: {activity_id}")
        except Exception as e:
            print(f"Error processing message: {e}")
            logging.error(f"Error processing message: {e}")

