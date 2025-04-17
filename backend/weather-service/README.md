# Weather Service

## Overview

The **Weather Service** is a microservice responsible for acquiring weather data for each activity segment, and publishing the results to Kafka. This service is part of the **TRAILMETRICS** project and interacts with Kafka, and external APIs: Openweather One Call API 3.0 (https://openweathermap.org/api/one-call-3). This service requires a business account and an api key as request parameter for authentication
The Free plan limit is `60 calls / minute`, `1000 free calls / day` and after that limit `0.0014 EUR / call`.

### Handle request limit
Since the Openweather API has a limit in free calls per day, and also a limit of calls per minute, the service handles the retry by sending a message to a Kafka retry queue

## Setup

### Install Dependencies

The service runs on **Python 3.10+**. First, create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Create the `.env` File

The `.env` file contains environment variables required for the service. **Do not commit this file to Git!** Create a `.env` file in the root of `weather-service/` with:

```
KAFKA_BROKER=localhost:9092
KAFKA_CONSUMER_GROUP=weather-service-group
KAFKA_RETRY_CONSUMER_GROUP=weather-service-retry-group
KAFKA_TOPIC_INPUT=segmentation-output-queue
KAFKA_TOPIC_OUTPUT=weather-output-queue
KAFKA_TOPIC_RETRY=weather-retry-queue
KAFKA_MAX_POLL_RECORDS=10
DISTANCE_THRESHOLD= 10000
ELEVATION_THRESHOLD=400
TIME_THRESHOLD=3600
OPENWEATHER_HISTORY_API_URL=https://api.openweathermap.org/data/3.0/onecall/timemachine
OPENWEATHER_API_KEY=your_api_key
DAILY_REQUEST_LIMIT=1000
```

### Running Locally

After setting up the environment, start the service with:

```bash
python app.py
```

## Running with Docker

To run the service inside a Docker container:

```bash
docker-compose up --build weather-service
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
