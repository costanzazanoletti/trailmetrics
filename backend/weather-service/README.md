# Weather Service

## Overview

The **Weather Service** is a microservice responsible for acquiring weather data for each activity segment, and publishing the results to Kafka. This service is part of the **TRAILMETRICS** project and interacts with Kafka, and external APIs: GribStream Historical Forecast API (https://gribstream.com/). This service requires a Bearer authentication and has a limit of request computed in credits
```
Credits = hours * parameters * (1 + (coordinates-1) / 500)
```
Or in words, hours of data, times the number of weather parameters, times bundles of 500 coordinates.

The Free plan limit is `1200 credits / day` and there's the option of purchasing a Pro Plan.

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
KAFKA_CONSUMER_GROUP=weather-service-group
KAFKA_TOPIC_INPUT=segmentation-output-queue
KAFKA_TOPIC_OUTPUT=weather-output-queue
KAFKA_MAX_POLL_RECORDS=10
WEATHER_HISTORY_API_URL=https://gribstream.com/api/v2/gfs/history
API_KEY=f10a6a334f76374d74c1e4df9260d828af2bedfa
DISTANCE_THRESHOLD= 10000
ELEVATION_THRESHOLD=400
TIME_THRESHOLD=3600
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
