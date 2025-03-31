import logging_setup
import logging
from app.kafka_consumer import start_kafka_consumer, start_kafka_retry_consumer
import threading
import sys
import signal

logger = logging.getLogger("app")
logger.info("Weather service started successfully")

# Global event to signal shutdown
shutdown_event = threading.Event()

def start_consumers():
    # Create threads to run both consumers concurrently
    consumer_thread = threading.Thread(target=start_kafka_consumer, args=(shutdown_event,))
    retry_consumer_thread = threading.Thread(target=start_kafka_retry_consumer, args=(shutdown_event,))
    
    # Start both consumer threads
    consumer_thread.start()
    retry_consumer_thread.start()

    # Wait for both threads to finish
    consumer_thread.join()
    retry_consumer_thread.join()

def graceful_shutdown(signum, frame):
    """Gracefully shuts down the Kafka consumers and exits."""
    logger.info("Gracefully shutting down...")
    
    # Signal the consumer threads to stop
    shutdown_event.set()

    # Optionally, you can give time for threads to clean up before exiting
    logger.info("Cleanup complete. Exiting gracefully.")
    sys.exit(0)  # Exit the program

if __name__ == "__main__":
    # Register the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, graceful_shutdown)

    # Start the consumers
    start_consumers()
