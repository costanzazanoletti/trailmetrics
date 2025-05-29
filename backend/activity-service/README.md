# Activity Service

This microservice is responsible for synchronizing the user's activities from Strava, orchestrating
the initial processing workflow, and serving as the main API provider for the frontend. It exposes
REST APIs (secured with JWT) and communicates with other backend services via Kafka events.

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

Configuration variables must be defined in a `.env` file. An example file is available at
`.env.example`.

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
- `efficiency-zone-request-queue`- produced if segments need efficiency zone computation

## Strava API Usage

This service integrates with Strava's public REST API to fetch activity data on behalf of
authenticated users. Specifically, it uses the following endpoints:

### [GET /athlete/activities](https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities)

Retrieves a paginated list of activity metadata for the authenticated user. The service uses query
parameters such as:

- `before` and `after` (UNIX timestamps) to filter the activity time window
- `page` and `per_page` for pagination

Used in: `StravaClient.fetchUserActivities(...)`

---

### [GET /activities/{id}/streams](https://developers.strava.com/docs/reference/#api-Streams-getActivityStreams)

Retrieves detailed time-series data ("streams") for a specific activity, including:

- GPS coordinates (`latlng`), distance, time
- Altitude, velocity, heart rate, cadence, power, temperature
- Grade (slope) and moving flag

Used in: `StravaClient.fetchActivityStream(...)`

---

[GET /activities/{id}](https://developers.strava.com/docs/reference/#api-Activities-getActivityById)  
Currently commented out, this endpoint would return full metadata for a single activity.

---

### Strava API Rate Limits

Strava enforces API usage limits based on registered application credentials:

- **Per 15-minute window**: 200 requests (100 read)
- **Per day**: 2,000 requests (1,000 read)

These limits are applied per access token and enforced globally across all users of the same client
ID. Exceeding these limits will result in `HTTP 429 Too Many Requests`.

The service should be designed to:

- Monitor the `X-RateLimit-Limit` and `X-RateLimit-Usage` headers returned in each API response.
- Apply backoff or delay logic if approaching the 15-min or daily threshold.
- Optionally queue or defer low-priority sync operations if rate saturation occurs.

More
details: [Strava API Rate Limits Documentation](https://developers.strava.com/docs/rate-limits/)

## Tests

Unit and integration tests are included under `src/test/`. Run them using:

```bash
./mvnw test
```
