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
- **Value JSON**: 
```json
{
    "userId": "28658549",
    "scheduledRetryTime": 1740680052.920566000,
    "sentTimestamp": 1740680052.920566000
  }
```
### `activity-stream-queue`

- **Description**: An activity has been synchronized and the processing has started
- **Producer Service**: `activity-service`
- **Consumer Service**: `segmentation-service`
- **Consumer Group**: `segmentation-service-group`
- **Key**: `activityId`
- **Value JSON**:
  ```json
  {
    "activityId": 13484124195,
    "userId": 12345,
    "startDate": 1740680048.270867,
    "processedAt": 1740680048.270867000,
    "compressedStream": "H4sIAAAAAAAA/+1c644muW19l/397UAXSpTyKoYRDOxN"
  }
  ```
  
### `segmentation-output-queue`

**Description:** An activity has been segmented  
**Producer Service:** `segmentation-service`  
**Consumer Service:** `terrain-service`, `weather-service`, `efficiency-service`  
**Consumer Group:** `terrain-service-group`,`weather-service-group`, `efficiency-service-group`  
**Key:** `activityId`  
**Value JSON:**

```json
{
  "activityId": 13484124195,
  "userId": 12345,
  "startDate": 1740680048.270867,
  "processedAt": 1740680048.270867,
  "compressedSegments": "H4sIAAAAAAAA/+1c644muW19l/397UAXSpTyKoYRDOxN"
}
```

### `terrain-output-queue`

**Description:** Terrain data has been retrieved from API
**Producer Service:** `terrain-service`  
**Consumer Service:** `efficiency-service`  
**Consumer Group:** `efficiency-service-group`  
**Key:** `activityId`  
**Value JSON:**

```json
{
  "activityId": 13484124195,
  "compressedTerrainInfo": "H4sIAAAAAAAA/+1c644muW19l/397UAXSpTyKoYRDOxN"
}
```

### `weather-output-queue`

**Description:** Weather data has been retrieved from API  
**Producer Service:** `weather-service`  
**Consumer Service:** `efficiency-service`  
**Consumer Group:** `efficiency-service-group`  
**Key:** `activityId`  
**Value JSON:**

```json
{
  "activityId": 13484124195,
  "compressedWeatherInfo": "H4sIAAAAAAAA/+1c644muW19l/397UAXSpTyKoYRDOxN"
}
```

### `weather-retry-queue`

**Description:** Weather API rate limit hit, retry after a delay  
**Producer Service:** `weather-service`  
**Consumer Service:** `weather-service`  
**Consumer Group:** `weather-service-group`  
**Key:** `activityId`  
**Value JSON:**

```json
{
  "activityId": 12345,
  "requestParams": {
    "lat": 46.0,
    "lon": 8.0,
    "dt": 1633595280,
    "units": "metric"
  },
  "segmentIds": ["123456-1","123456-2"],
  "retryTimestamp": 1743416209
}
```

### `user-activities-changed-queue`

**Description:** There are changes in a user's activities 
**Producer Service:** `activity-service-group`
**Consumer Service:** `efficiency-service`
**Consumer Group:** `efficiency-service-group`  
**Key:** `userId`  
**Value JSON:**

```json
{
  "userId": "28658549",
  "checkedAt": 1740680052.987654,
  "newActivityIds": [1234, 5678],
  "deletedActivityIds": [4321, 8765]
}
```
