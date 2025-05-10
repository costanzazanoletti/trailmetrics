# Weather Service

## Overview

The **Weather Service** is a Python-based microservice responsible for enriching activity segments with historical weather data. It consumes segment data from Kafka, queries OpenWeather One Call API 3.0, and publishes enriched data downstream.

## Responsibilities

- Consumes segmentation results from `segmentation-output-queue`
- Uses coordinates, elevation changes and timestamps to fetch historical weather from OpenWeather
- Handles API rate limits by deferring requests via a retry Kafka topic
- Publishes weather-enriched data to `weather-output-queue`

## External API: OpenWeather One Call 3.0

This service uses the **OpenWeather One Call API 3.0** ([docs](https://openweathermap.org/api/one-call-3)) to fetch historical weather.

- Endpoint: `https://api.openweathermap.org/data/3.0/onecall/timemachine`
- Requires API Key passed via query string (`appid=...`)
- **Free plan limits:**

  - 60 calls/minute
  - 1000 calls/day (free)
  - Exceeding daily limit: €0.0014 per call

## Rate Limit Handling

To respect API usage limits, the service tracks requests and defers over-quota segments via `weather-retry-queue`. These are automatically retried after a configurable delay.

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

Environment variables are defined in a `.env` file. A template is available in `.env.example`.

These include:

- Kafka broker, topics, consumer groups
- OpenWeather API base URL and key
- Request limits and retry strategy
- Segment filtering thresholds (distance, elevation, time)

## Running Locally

```bash
python app.py
```

## Running with Docker

```bash
docker compose up weather-service
```

To rebuild:

```bash
docker compose up --build -d weather-service
```

## Kafka Topics

- Consumes: `segmentation-output-queue`
- Produces: `weather-output-queue`
- Retry: `weather-retry-queue`

## Tests

Run tests with:

```bash
pytest -s tests/
```

## More Information

For overall architecture, see the [Developer Guide](../../docs/developer-guide.md).
