# TrailMetrics - Project Documentation

## 1. Introduction

**TrailMetrics** is an application for analyzing and processing trail running training and race activities. The system uses **Kafka** for real-time messaging, **PostgreSQL** for data storage, and **Spring Boot** for backend processing and API exposure.

**Technologies used:**

- **Kafka (Kraft)**: Real-time message processing.
- **Spring Boot**: Backend framework.
- **Python**: Metrics computation
- **PostgreSQL**: Data storage for activities.
- **Docker**: Containerization of services.

## 2. System Architecture

The system uses a **microservices architecture** with the following components:

- **Backend**: Spring Boot processes activity data and integrates with Kafka for real-time messaging.
- **Kafka**: Handles real-time messaging and data processing via producer and consumer.
- **PostgreSQL**: Stores activities and user data.

## 3. Setup Instructions

### 3.1. Prerequisites

- **Docker and Docker Compose**: To run frontend, backend, data analysis, Kafka and PostgreSQL containers.
- **Java 17+**: To run the Spring Boot backend.
- **Maven**: For Spring Boot dependency management.

### 3.2. Clone the Repository

```bash
git clone https://github.com/your-username/trailmetrics.git
```

### 3.3. Run the Project with Docker Compose

1. Navigate to the project directory:

```bash
cd trailmetrics
```

2. Start the services:

```bash
docker-compose up -d
```

3. Verify that the containers are running:

```bash
docker ps
```

## 4. Kafka Configuration

### 4.1. Kafka (Kraft)

Kafka is configured to **handle topics** and process messages via **producer** and **consumer**.

- **Kafka Port**: `localhost:9092`

## 5. Kafka Topics and Messages

This table defines the Kafka topics and messages used in the application for event-driven communication between services.

### 5.1 Kafka Messages

# Kafka Topics and Messages

This document defines the Kafka topics and messages used in the application for event-driven communication between services.

# Kafka Topics and Messages

This document defines the Kafka topics and messages used in the application for event-driven communication between services.

## Kafka Messages

### `activity-processing-started-queue`

- **Description**: An activity has been synchronized and the processing has started
- **Producer Service**: `activity-service`
- **Consumer Service**: `segmentation-service`
- **Consumer Group**: `segmentation-service-group`
- **Key**: `activityId`
- **Value JSON**:
  ```json
  {
    "activityId": 13484124195,
    "processedAt": 1740680048.270867000
  }
  ```

### `activity-sync-queue`

- **Description**: Syncing activity data
- **Producer Service**: `activity-service`
- **Consumer Service**: `activity-service`
- **Consumer Group**: `activity-service-group`
- **Key**: `activityId`
- **Value JSON**:
  ```json
  {
    "userId": "28658549",
    "activityId": 8054008512,
    "timestamp": 1740680052.920566000
  }
  ```

### `activity-retry-queue`

- **Description**: Retry failed activity syncs
- **Producer Service**: `activity-service`
- **Consumer Service**: `activity-service`
- **Consumer Group**: `activity-service-group`
- **Key**: `activityId`
- **Value JSON**:
  ```json
  {
    "userId": "28658549",
    "activityId": 8054008512,
    "timestamp": 1740680052.920566000
  }
  ```

### `user-sync-retry-queue`

- **Description**: Retry failed user syncs
- **Producer Service**: `activity-service`
- **Consumer Service**: `activity-service`
- **Consumer Group**: `user-service-group`
- **Key**: `userId`
- **Value JSON**: `UserSyncMessage`

### `activity-terrain-request-queue`

**Description:** Request for terrain data collection  
**Producer Service:** `segmentation-service`  
**Consumer Service:** `terrain-service`  
**Consumer Group:** `terrain-service-group`  
**Key:** `activityId`  
**Value JSON:**

```json
{
  "activityId": 13484124195,
  "requestedAt": 1740680048.270867
}
```

### `activity-weather-request-queue`

**Description:** Request for weather data collection  
**Producer Service:** `segmentation-service`  
**Consumer Service:** `weather-service`  
**Consumer Group:** `weather-service-group`  
**Key:** `activityId`  
**Value JSON:**

```json
{
  "activityId": 13484124195,
  "requestedAt": 1740680048.270867
}
```

### `activity-terrain-processed-queue`

**Description:** Terrain data has been stored in the database  
**Producer Service:** `terrain-service`  
**Consumer Service:** `efficiency-service`  
**Consumer Group:** `efficiency-service-group`  
**Key:** `activityId`  
**Value JSON:**

```json
{
  "activityId": 13484124195,
  "processedAt": 1740680050.123456
}
```

### `activity-meteo-processed-queue`

**Description:** Weather data has been stored in the database  
**Producer Service:** `weather-service`  
**Consumer Service:** `efficiency-service`  
**Consumer Group:** `efficiency-service-group`  
**Key:** `activityId`  
**Value JSON:**

```json
{
  "activityId": 13484124195,
  "processedAt": 1740680051.654321
}
```

### `activity-processing-completed-queue`

**Description:** All required data for efficiency computation is available  
**Producer Service:** `efficiency-service-group`
**Consumer Service:** TO BE DEFINED
**Consumer Group:** `efficiency-service-group`  
**Key:** `activityId`  
**Value JSON:**

```json
{
  "activityId": 13484124195,
  "completedAt": 1740680052.987654
}
```
