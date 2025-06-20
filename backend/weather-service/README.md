# Weather Service

## Overview

The **Weather Service** is a Python-based microservice responsible for enriching activity segments with both historical and forecast weather data. It consumes segments from Kafka, queries various OpenWeather APIs depending on activity timing (past or planned), and publishes the enriched weather data downstream. It also manages API rate limits gracefully via retry queues.

## Responsibilities

- Consumes segment data from `segmentation-output-queue`
- Dynamically selects the appropriate OpenWeather API:
  - **Historical** (for past activities)
  - **Hourly/Daily Forecast** (for upcoming activities)
  - **Summary API** (for activities scheduled far in the future)
- Enriches each segment with relevant weather variables (e.g., temperature, wind, humidity, precipitation)
- Publishes results to `weather-output-queue` or defers over-limit requests to `weather-retry-queue`

## External APIs: OpenWeather

This service integrates with multiple OpenWeather endpoints, depending on activity type and date:

| **API Type** | **Endpoint**                                      | **Use Case**                          |
| ------------ | ------------------------------------------------- | ------------------------------------- |
| Historical   | `/timemachine` (One Call 3.0 API)                 | For past activity weather             |
| Hourly       | `/onecall?exclude=current,minutely,daily,alerts`  | High-resolution forecasts (up to 48h) |
| Daily        | `/onecall?exclude=current,minutely,hourly,alerts` | Daily forecast (up to 8 days)         |
| Summary      | `/summary` (Daily Aggregation API)                | Long-range planned activities         |

Each request includes segment coordinates and a reference timestamp to retrieve the most relevant data.

## Rate Limit Handling

To comply with OpenWeather's free-tier quota (1000 requests/day), the service maintains an internal request counter (`RequestCounter`). If the quota is exceeded:

- Segments are redirected to the `weather-retry-queue`
- A retry mechanism with configurable delay ensures deferred processing

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
