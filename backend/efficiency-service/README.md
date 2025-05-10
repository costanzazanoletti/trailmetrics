# Efficiency Service

## Overview

The **Efficiency Service** is a Python-based microservice responsible for:

- Consuming activity segment data from Kafka (`segmentation-output-queue`, `terrain-output-queue`, `weather-output-queue`, etc.)
- Saving terrain, weather, and segment information to the database
- Calculating a custom efficiency score for each segment
- Managing analysis state per activity
- Computing segment similarity within a user's activities based on grade category and predefined metrics

This service operates fully asynchronously and reacts to Kafka events published by other services.

## Setup

### Prerequisites

- Python 3.10+

### Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Configuration

All environment variables must be defined in a `.env` file. An example is provided in `.env.example`. This includes:

- Kafka topic and broker configuration
- PostgreSQL database URL
- Weights and parameters for efficiency score computation and similarity analysis

## Running Locally

After setting up the environment:

```bash
python app.py
```

## Running with Docker

Build and run the service with:

```bash
docker compose up efficiency-service
```

If dependencies or Dockerfile changed:

```bash
docker compose up --build -d efficiency-service
```

## Database Connection

The service connects to the central PostgreSQL database using the `analytics_user`. The database and user are created automatically when running in Docker.

For local setup, see the database service README and run the SQL init scripts manually if needed.

## Tests

Tests are located in the `tests/` folder and use a separate PostgreSQL test instance defined in the `.env`.

Run tests with:

```bash
pytest -s tests/
```

## Related Topics

- Kafka topics consumed:

  - `segmentation-output-queue`
  - `terrain-output-queue`
  - `weather-output-queue`
  - `activities-deleted-queue`

- The similarity matrix computation runs only when all required data for a user activity is available.

## More Information

For system-wide architecture and integration, refer to the [Developer Guide](../../docs/developer-guide.md).
