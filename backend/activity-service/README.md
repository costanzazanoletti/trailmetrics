# Activity Service

This service synchronizes user's activities with Strava API and saves them into the database.
It can be called by the frontend through REST API, authenticated with JWT.
The JWT and Strava access token are managed by Authentication Service and Activity Service requests them through REST API, authenticated with API Key.
Activity Service produces and consumes Kafka messages to synchronize single activity streams of data and to signal that an activity has been processed.

## Depends on

- Kafka
- PostgreSQL Database
- Authentication Service

## Build

The configuration properties are externalized in a .env file that must be created before building the application
Some properties are overloaded by docker-compose.yml when the application runs inside Docker.
The service can run in IntelliJ or in Docker. To run in Docker generate the jar through IntelliJ maven `clean package`.
