# Terrain Service

## Overview

The **Terrain Service** is a Python-based microservice responsible for enriching activity segments with terrain type information using OpenStreetMap data. It listens to processed segment messages from Kafka and queries the Overpass API to determine terrain characteristics.

## Responsibilities

- Consumes segment messages from `segmentation-output-queue`
- Queries Overpass API to detect surface and path type
- Attaches terrain classification to each segment
- Publishes enriched data to `terrain-output-queue`

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

All environment variables must be provided in a `.env` file. A sample is available in `.env.example`. Configuration includes:

- Kafka broker and topic names
- Overpass API URL
- Polling batch size

## Running Locally

After environment setup:

```bash
python app.py
```

## Running with Docker

```bash
docker compose up terrain-service
```

To rebuild:

```bash
docker compose up --build -d terrain-service
```

## Kafka Topics

- Consumes: `segmentation-output-queue`
- Produces: `terrain-output-queue`

## External APIs

- OpenStreetMap Overpass API: queried via HTTP (no authentication required)

  - Default: `http://overpass-api.de/api/interpreter`

## Tests

Tests are in the `tests/` folder. Run them with:

```bash
pytest -s tests/
```

## More Information

For overall system documentation, refer to the [Developer Guide](../../docs/developer-guide.md).
