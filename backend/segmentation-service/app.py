from app.kafka_consumer import start_kafka_consumer
import logging_setup
import logging

logger = logging.getLogger("segmentation")
logger.info("Segmentation service started successfully")


if __name__ == "__main__":
    start_kafka_consumer()