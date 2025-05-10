# Segmentation Service

## Overview

The **Segmentation Service** is a Python-based microservice responsible for analyzing activity streams and dividing the route into segments based on elevation profile and gradient. It processes incoming messages from Kafka and publishes enriched segment data to downstream services.

## Responsibilities

- Consumes activity stream data from `activity-stream-queue`
- Applies slope-based segmentation logic using configured thresholds
- Assigns grade category and cadence thresholds to segments
- Publishes results to `segmentation-output-queue`

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

All configuration parameters must be provided via a `.env` file. A reference template is available in `.env.example`. These include:

- segmentation thresholds (min/max length, gradient tolerance)
- cadence classification parameters
- Kafka broker, consumer group, input/output topics

## Running Locally

After setting up the environment:

```bash
python app.py
```

## Running with Docker

```bash
docker compose up segmentation-service
```

If dependencies or Dockerfile changed:

```bash
docker compose up --build -d segmentation-service
```

## Kafka Topics

- Consumes: `activity-stream-queue`
- Produces: `segmentation-output-queue`

## Tests

Unit tests are available in the `tests/` folder.

Run tests with:

```bash
pytest -s tests/
```

## More Information

For full system context, see the [Developer Guide](../../docs/developer-guide.md).
