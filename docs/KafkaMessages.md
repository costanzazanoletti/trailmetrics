# Kafka Topics and Messages

This document defines the Kafka topics and messages used in TrailMetrics for event-driven communication between services.

---

### `activity-sync-queue`

- **Description**: Syncing activity data
- **Producer**: `activity-service`
- **Consumer**: `activity-service`
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

---

### `activity-retry-queue`

- **Description**: Retry failed activity syncs
- **Producer**: `activity-service`
- **Consumer**: `activity-service`
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

---

### `user-sync-retry-queue`

- **Description**: Retry failed user syncs
- **Producer**: `activity-service`
- **Consumer**: `activity-service`
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

---

### `activity-stream-queue`

- **Description**: An activity has been synchronized and processing has started
- **Producer**: `activity-service`
- **Consumer**: `segmentation-service`
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

---

### `segmentation-output-queue`

- **Description**: Activity segmentation completed
- **Producer**: `segmentation-service`
- **Consumer**: `terrain-service`, `weather-service`, `efficiency-service`
- **Consumer Groups**: `terrain-service-group`, `weather-service-group`, `efficiency-service-group`
- **Key**: `activityId`
- **Value JSON**:

```json
{
  "activityId": 13484124195,
  "userId": 12345,
  "startDate": 1740680048.270867,
  "processedAt": 1740680048.270867,
  "status": "success",
  "compressedSegments": "H4sIAAAAAAAA/+1c644muW19l/397UAXSpTyKoYRDOxN"
}
```

---

### `terrain-output-queue`

- **Description**: Terrain data retrieved
- **Producer**: `terrain-service`
- **Consumer**: `efficiency-service`
- **Consumer Group**: `efficiency-service-group`
- **Key**: `activityId`
- **Value JSON**:

```json
{
  "activityId": 13484124195,
  "compressedTerrainInfo": "H4sIAAAAAAAA/+1c644muW19l/397UAXSpTyKoYRDOxN"
}
```

---

### `weather-output-queue`

- **Description**: Weather data retrieved
- **Producer**: `weather-service`
- **Consumer**: `efficiency-service`
- **Consumer Group**: `efficiency-service-group`
- **Key**: `activityId`
- **Value JSON**:

```json
{
  "activityId": 13484124195,
  "compressedWeatherInfo": "H4sIAAAAAAAA/+1c644muW19l/397UAXSpTyKoYRDOxN"
}
```

---

### `weather-retry-queue`

- **Description**: Weather API rate limit hit, retry scheduled
- **Producer**: `weather-service`
- **Consumer**: `weather-service`
- **Consumer Group**: `weather-service-group`
- **Key**: `activityId`
- **Value JSON**:

```json
{
  "activityId": 12345,
  "requestParams": {
    "lat": 46.0,
    "lon": 8.0,
    "dt": 1633595280,
    "units": "metric"
  },
  "segmentIds": ["123456-1", "123456-2"],
  "retryTimestamp": 1743416209
}
```

---

### `activities-deleted-queue`

- **Description**: List of deleted activities
- **Producer**: `activity-service`
- **Consumer**: `efficiency-service`
- **Consumer Group**: `efficiency-service-group`
- **Key**: `userId`
- **Value JSON**:

```json
{
  "userId": "28658549",
  "checkedAt": 1740680052.987654,
  "deletedActivityIds": [4321, 8765]
}
```
