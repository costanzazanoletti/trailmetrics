import logging_setup
import logging
import threading
import sys
import signal
from app.database import check_segments_table
from app.kafka_consumer import start_kafka_segments_consumer, start_kafka_terrain_consumer, start_kafka_weather_consumer

logger = logging.getLogger("app")
logger.info("Efficiency service started successfully")

# Global event to signal shutdown
shutdown_event = threading.Event()

def start_consumers():
    # Create threads to run all consumers concurrently
    segment_consumer_thread = threading.Thread(target=start_kafka_segments_consumer, args=(shutdown_event,))
    terrain_consumer_thread = threading.Thread(target=start_kafka_terrain_consumer, args=(shutdown_event,))
    weather_consumer_thread = threading.Thread(target=start_kafka_weather_consumer, args=(shutdown_event,))
    
    # Start all consumer threads
    segment_consumer_thread.start()
    terrain_consumer_thread.start()
    weather_consumer_thread.start()

    # Wait for all threads to finish
    segment_consumer_thread.join()
    terrain_consumer_thread.join()
    weather_consumer_thread.join()

def graceful_shutdown(signum, frame):
    """Gracefully shuts down the Kafka consumers and exits."""
    logger.info("Gracefully shutting down...")
    
    # Signal the consumer threads to stop
    shutdown_event.set()

    # Optionally, you can give time for threads to clean up before exiting
    logger.info("Cleanup complete. Exiting gracefully.")
    sys.exit(0)  # Exit the program

if __name__ == "__main__":
    print("Efficiency service started successfully")
    check_segments_table()
    start_consumers()