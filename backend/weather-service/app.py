import logging_setup
import logging
from app.kafka_consumer import start_kafka_consumer

logger = logging.getLogger("app")
logger.info("Weather service started successfully")


if __name__ == "__main__":
    start_kafka_consumer()