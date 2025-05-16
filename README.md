# TrailMetrics

A microservice-based platform for analyzing trail running performance data. TrailMetrics processes data from wearable devices and public APIs (Strava, weather, terrain) to compute individual efficiency metrics and suggest optimal pacing strategies for runners.

![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 1. Introduction

TrailMetrics is a web-based application for analyzing trail running training and race activities. It computes a custom efficiency metric over route segments that are homogeneous in terms of grade, terrain type, and weather conditions. By comparing performance across similar segments, TrailMetrics helps athletes interpret their effort and optimize pacing strategies. The system leverages Kafka for real-time messaging, PostgreSQL for data storage, and a backend built with Spring Boot and Python.

## 2. Technologies

- **Kafka (KRaft)**: Real-time event streaming and coordination between microservices
- **Spring Boot**: Java-based backend services (auth, activity coordination)
- **Python**: Services for metrics computation and data enrichment
- **PostgreSQL**: Centralized data storage
- **React + Tailwind**: Frontend interface (in `frontend/`)
- **Docker Compose**: Container orchestration for local development

## 3. System Architecture

TrailMetrics follows a microservices architecture. The main components are:

- **Activity Service** – manages activity sync, retries, and orchestration
- **Segmentation Service** – splits activities by slope/terrain
- **Efficiency Service** – computes efficiency metrics and performance zones
- **Weather Service** – enriches data with weather forecast info
- **Terrain Service** – identifies terrain type via geographic data
- **Auth Service** – handles Strava OAuth2 login and user profiles
- **Frontend** – visualizes activities, graphs, maps, and planning tools

See [`docs/Architecture.png`](docs/Architecture.png) for a high-level overview.

## 4. Getting Started

### 4.1. Prerequisites

- Docker and Docker Compose
- Java 17+
- Maven

### 4.2. Clone and Run

```bash
git clone https://github.com/costanzazanoletti/trailmetrics.git
cd trailmetrics
docker compose up -d
```

Visit `http://localhost:3000` to access the frontend.

### Using Makefile (optional)

You can use the provided `Makefile` in the project root to simplify Docker operations:

```bash
make up         # Start all services
make down       # Stop and remove containers and volumes
make rebuild    # Full cleanup and rebuild
make logs s=auth-service         # View logs for a specific service
make shell s=efficiency-service  # Open a shell inside a service container
```

## 5. Project Structure

```
frontend/               → React app
backend/
  ├─ activity-service/   → Sync and orchestrate activities
  ├─ auth-service/       → Authentication and token handling
  ├─ efficiency-service/ → Efficiency computation
  ├─ segmentation-service/ → Grade/terrain segmentation
  ├─ terrain-service/    → Terrain classification
  ├─ weather-service/    → Weather enrichment
  ├─ database/           → Init scripts, schema, Docker setup
  └─ ...
docker-compose.yml     → Service orchestration
```

## 6. Kafka Topics Overview

Kafka coordinates microservice communication. The key topics used include:

- `activity-sync-queue`: triggers sync of new activities
- `activity-retry-queue`: retries failed syncs
- `user-sync-retry-queue`: retries failed user updates
- `activity-stream-queue`: raw stream ready for segmentation
- `segmentation-output-queue`: segment result broadcast
- `terrain-output-queue`: terrain info available
- `weather-output-queue`: weather info available
- `weather-retry-queue`: weather retry scheduling
- `activities-deleted-queue`: deleted activity list
- `efficiency-zone-request-queue`: deleted activity list

Each topic includes structured JSON messages. See [`docs/KafkaMessages.md`](docs/Kafkamessages.md) for full schemas.

## 7. Contributing

This project is part of a master's thesis and currently not accepting external contributions. However, feel free to open issues or suggestions.

## 8. License

MIT License.
