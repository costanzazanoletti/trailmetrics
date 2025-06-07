import logging_setup
import logging
import threading
import sys
import os
import signal
from apscheduler.schedulers.background import BackgroundScheduler
from services.efficiency_zone_service import run_efficiency_zone_batch
from services.recommendation_service import run_batch_prediction_all_users
from db.setup import engine
from app.kafka_consumer import (
    start_kafka_segments_consumer, 
    start_kafka_terrain_consumer, 
    start_kafka_weather_consumer, 
    start_kafka_deleted_activities_consumer,
    start_kafka_efficiency_zone_request_consumer
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ZONE_COMPUTATION_SCHEDULE = int(os.getenv("ZONE_COMPUTATION_SCHEDULE", "10"))

# Start logging service
logger = logging.getLogger("app")
logger.info("Efficiency service started successfully")

# Global event to signal shutdown
shutdown_event = threading.Event()

def start_consumers():
    # Create threads to run all consumers concurrently
    segment_consumer_thread = threading.Thread(target=start_kafka_segments_consumer, args=(shutdown_event,))
    terrain_consumer_thread = threading.Thread(target=start_kafka_terrain_consumer, args=(shutdown_event,))
    weather_consumer_thread = threading.Thread(target=start_kafka_weather_consumer, args=(shutdown_event,))
    deletion_consumer_thread = threading.Thread(target=start_kafka_deleted_activities_consumer, args=(shutdown_event,))
    efficiency_zone_consumer_thread = threading.Thread(target=start_kafka_efficiency_zone_request_consumer, args=(shutdown_event,))
    
    # Start all consumer threads
    segment_consumer_thread.start()
    terrain_consumer_thread.start()
    weather_consumer_thread.start()
    deletion_consumer_thread.start()
    efficiency_zone_consumer_thread.start()

    # Run one efficiency zone calculation batch immediately
    logger.info("Running initial batch efficiency zone calculation...")
    run_efficiency_zone_batch()
    # Run batch prediction immediately
    logger.info("Running initial batch prediction...")
    run_batch_prediction_all_users(engine)
    
    # Schedule batch efficiency zone calculation every 10 minutes
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_efficiency_zone_batch, 'interval', minutes=ZONE_COMPUTATION_SCHEDULE)
    scheduler.add_job(run_batch_prediction_all_users, 'interval', minutes=ZONE_COMPUTATION_SCHEDULE, args=[engine])

    scheduler.start()
    logger.info(f"Scheduled batch efficiency zone calculation every {ZONE_COMPUTATION_SCHEDULE} minutes")
    logger.info(f"Scheduled batch planned prediction every {ZONE_COMPUTATION_SCHEDULE} minutes")

    # Wait for all threads to finish
    try:
        segment_consumer_thread.join()
        terrain_consumer_thread.join()
        weather_consumer_thread.join()
        deletion_consumer_thread.join()
        efficiency_zone_consumer_thread.join()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down...")
        scheduler.shutdown(wait=False)
        graceful_shutdown(None, None)

def graceful_shutdown(signum, frame):
    """Gracefully shuts down the Kafka consumers and exits."""
    logger.info("Gracefully shutting down...")
    
    # Signal the consumer threads to stop
    shutdown_event.set()
    
    # Wait a bit to allow the threads to clean up (optional)
    logger.info("Cleanup complete. Exiting gracefully.")
    sys.exit(0)  # Exit the program

if __name__ == "__main__":   
    # Capture SIGINT (Ctrl-C) and perform graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    
    start_consumers()