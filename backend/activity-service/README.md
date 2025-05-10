# Activity Service

This microservice is responsible for synchronizing the user's activities from Strava, orchestrating the initial processing workflow, and serving as the main API provider for the frontend. It exposes REST APIs (secured with JWT) and communicates with other backend services via Kafka events.

## Responsibilities

- Pulls activity metadata and streams from Strava via Strava API
- Authenticates requests using JWT (validated via the Auth Service)
- Manages user access tokens by requesting them from the Auth Service using API Key authentication
- Stores activity metadata in PostgreSQL
- Serves activity-related data to the frontend via REST endpoints
- Publishes Kafka messages to initiate downstream processing (segmentation, efficiency, etc.)
- Consumes Kafka messages for retry and cleanup operations

## Dependencies

- Kafka (for inter-service communication)
- PostgreSQL (activity storage)
- Auth Service (token and JWT validation)

## Configuration

Configuration variables must be defined in a `.env` file. An example file is available at `.env.example`.

This includes:

- database connection details
- Kafka configuration
- API key for the Auth Service
- Strava API parameters
- encryption key and salt

## Building and Running

### From IntelliJ

1. Ensure `.env` file is present with required config (see `.env.example`)
2. Build using Maven: `clean package`
3. Run `ActivityServiceApplication` class directly

### With Docker

1. Build the jar with Maven:

```bash
./mvnw clean package
```

2. Start via Docker Compose:

```bash
docker compose up activity-service
```

## Kafka Topics Used

- `activity-sync-queue` – produced and consumed internally for activity sync trigger
- `activity-retry-queue` – retry sync if failed
- `user-sync-retry-queue` – retry user token fetch
- `activity-stream-queue` – emitted when activity stream is available
- `activities-deleted-queue` – consumed to clean deleted activities

## Tests

Unit and integration tests are included under `src/test/`. Run them using:

```bash
./mvnw test
```
