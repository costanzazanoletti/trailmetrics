# Developer Guide

## Project Overview

TrailMetrics is composed of multiple microservices implemented in Python and Java, orchestrated via Kafka and deployed locally using Docker Compose. Each service handles a distinct task in processing and analyzing trail running data.

## Environment Setup

### Docker

To run all services in detached mode:

```sh
docker-compose up -d
```

To shut down all containers:

```sh
docker-compose down
```

To build all Docker images:

```sh
docker-compose --build
```

To start and stop a single container (e.g., `auth-service`):

```sh
docker stop auth-service
docker start auth-service
```

### Python

To run a service:

```sh
python app.py
```

To run tests:

```sh
pytest tests/
```

To show output in terminal:

```sh
pytest -s tests/
```

## Database

### Backup & Restore

To create a PostgreSQL dump from Docker:

```sh
docker exec -t <postgres_container_id> pg_dump -U <db_user> -d <db_name> > dump_file_name.sql
```

## Kafka

### UI Access

Kafka topics and consumer groups can be inspected using AKHQ:

```sh
http://localhost:9080
```

## Logs & Debug

To read logs from a container (e.g., `auth-service`):

```sh
docker exec -it auth-service cat /app/logs/app.logs
```

## Diagrams

Diagram sources are provided in `.drawio` format inside the `docs/` folder. These can be edited using [draw.io](https://app.diagrams.net/). The `.png` files are generated images used for quick viewing.
