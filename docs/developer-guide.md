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

## Scheduled Batch Jobs

The Efficiency Service includes an internal scheduler based on [APScheduler](https://apscheduler.readthedocs.io/), which computes and updates efficiency zones for running segments.

### Behavior

- At startup, the service immediately performs a full efficiency zone update for all segments whose similarity data has been recently computed.
- After that, it runs every 10 minutes (configurable via environment variable), checking for any segments that are:
  - New
  - Previously unprocessed
  - Affected by updated similarity data

Only those segments are processed and written to the `segment_efficiency_zone` table.

### Production Considerations

By default, the scheduler runs **in-process**, so it works seamlessly in development or single-container deployments. However, in production environments with multiple replicas (e.g. Kubernetes, Gunicorn workers, Heroku dynos), this can cause **duplicate batch jobs**.

Recommended strategies:

- **Single-instance deployment:** no action needed.
- **Multiple replicas:** run the scheduler only in a dedicated container or worker.
- Alternatively, move the job logic to an external orchestrator like **Celery Beat**, **Kubernetes CronJob**, or **Airflow**.

If needed, you can disable the scheduler by commenting out the related lines in `app.py` inside the Efficiency Service.

## Logs & Debug

To read logs from a container (e.g., `auth-service`):

```sh
docker exec -it auth-service cat /app/logs/app.logs
```

## Diagrams

Diagram sources are provided in `.drawio` format inside the `docs/` folder. These can be edited using [draw.io](https://app.diagrams.net/). The `.png` files are generated images used for quick viewing.
