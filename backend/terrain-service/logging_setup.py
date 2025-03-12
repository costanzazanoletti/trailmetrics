import logging
import logging.config
import os

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Load logging configuration
logging.config.fileConfig("logging.conf")

# Create a logger instance for the service
logger = logging.getLogger("app")

logger.info("Logging setup complete. Logger Initialized.")
