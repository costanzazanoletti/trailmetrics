# Segmentation Service

## Overview

The **Segmentation Service** is a microservice responsible for processing activity data, segmenting the route based on elevation changes, and publishing the results to Kafka. This service is part of the **TRAILMETRICS** project and interacts with Kafka.

## Setup

### Install Dependencies

The service runs on **Python 3.10+**. First, create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Create the `.env` File

The `.env` file contains environment variables required for the service. **Do not commit this file to Git!** Create a `.env` file in the root of `segmentation-service/` with:
```
GRADIENT_TOLERANCE=0.5
MIN_SEGMENT_LENGTH=50.0
MAX_SEGMENT_LENGTH=200.0
CLASSIFICATION_TOLERANCE=2.5
CADENCE_THRESHOLD=60
CADENCE_TOLERANCE=5
ROLLING_WINDOW_SIZE=0
KAFKA_BROKER=localhost:9092
KAFKA_CONSUMER_GROUP=segmentation-service-group
KAFKA_TOPIC_INPUT=activity-stream-queue
KAFKA_TOPIC_OUTPUT=segmentation-output-queue
```

### Running Locally

After setting up the environment, start the service with:

```bash
python app.py
```

## Running with Docker

To run the service inside a Docker container:

```bash
docker-compose up --build segmentation-service
```

If you made changes to `requirements.txt` or `Dockerfile`, rebuild:

```bash
docker-compose up --build -d
```

## Tests

### Running tests
To test the service, activate the virtual environment and run:

```bash
pytest -s tests/
```

## More Information

For a complete setup of **TRAILMETRICS**, check the [Developer Guide](../../docs/developer-guide.md).
