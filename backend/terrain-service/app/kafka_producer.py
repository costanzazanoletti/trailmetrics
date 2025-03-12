import json
import os
import base64
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
