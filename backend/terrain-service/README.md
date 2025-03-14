# Terrain Service

## Overview

The **Terrain Service** is a microservice responsible for processing activity data, segmenting the route based on elevation changes, and publishing the results to Kafka. This service is part of the **TRAILMETRICS** project and interacts with Kafka, and external APIs: OpenStreetMap Overpass interpreter. This API doesn't require any authentication.

## Setup

### Install Dependencies

The service runs on **Python 3.10+**. First, create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Create the `.env` File

The `.env` file contains environment variables required for the service. **Do not commit this file to Git!** Create a `.env` file in the root of `terrain-service/` with:

```
KAFKA_BROKER=localhost:9092
KAFKA_CONSUMER_GROUP=terrain-service-group
KAFKA_TOPIC_INPUT=segmentation-output-queue
KAFKA_TOPIC_OUTPUT=terrain-output-queue
KAFKA_MAX_POLL_RECORDS=10
OVERPASS_API_URL=http://overpass-api.de/api/interpreter
```

### Running Locally

After setting up the environment, start the service with:

```bash
python app.py
```

## Running with Docker

To run the service inside a Docker container:

```bash
docker-compose up --build terrain-service
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
