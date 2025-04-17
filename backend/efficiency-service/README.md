# Efficiency Service

## Overview
The **Efficiency Service** is a microservice responsible for collecting all the information from the other services (segments, terrain, weather), save the information into the database and compute the efficiency metrics, the similarity within segments and the performance zones.

## Setup

### Install Dependencies

The service runs on **Python 3.10+**. First, create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Create the `.env` File

The `.env` file contains environment variables required for the service. **Do not commit this file to Git!** Create a `.env` file in the root of `efficiency-service/` with:
DATABASE_URL=postgresql://analytics_user:[password]@localhost:5432/trailmetrics
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/trailmetrics_test
KAFKA_BROKER=localhost:9092
KAFKA_CONSUMER_GROUP=efficiency-service-group
KAFKA_TOPIC_SEGMENTS=segmentation-output-queue
KAFKA_TOPIC_TERRAIN=terrain-output-queue
KAFKA_TOPIC_WEATHER=weather-output-queue
KAFKA_TOPIC_DELETED_ACTIVITIES=activities-deleted-queue
EFFICIENCY_FACTOR_SCALE=10
EFFICIENCY_ELEVATION_WEIGHT=1
EFFICIENCY_FACTOR_HR_DRIFT_WEIGHT=1

## Database connection
The service connects to the application PostgreSQL database with a dedicated user (**analytics_user**).

When running with docker-compose, the database and users are created and configured through dedicated scripts. When running locally you can launch the scripts located in the /database folder.

### Running Locally

After setting up the environment, start the service with:

```bash
python app.py
```

## Running with Docker

To run the service inside a Docker container:

```bash
docker-compose up efficiency-service
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
## Test database
The .env file should contain the url of the PostgreSQL test database that is automatically used when the tests are launched with pytest.

## More Information

For a complete setup of **TRAILMETRICS**, check the [Developer Guide](../../docs/developer-guide.md).