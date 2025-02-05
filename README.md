# TrailMetrics - Project Documentation

## 1. Introduction

**TrailMetrics** is an application for analyzing and processing trail running training and race activities. The system uses **Kafka** for real-time messaging, **PostgreSQL** for data storage, and **Spring Boot** for backend processing and API exposure.

**Technologies used:**
- **Kafka (Kraft)**: Real-time message processing.
- **Spring Boot**: Backend framework.
- **PostgreSQL**: Data storage for activities.
- **Docker**: Containerization of services.

## 2. System Architecture

The system uses a **microservices architecture** with the following components:
- **Backend**: Spring Boot processes activity data and integrates with Kafka for real-time messaging.
- **Kafka**: Handles real-time messaging and data processing via producer and consumer.
- **PostgreSQL**: Stores activities and user data.

## 3. Setup Instructions

### 3.1. Prerequisites

- **Docker and Docker Compose**: To run Kafka, Zookeeper, and PostgreSQL containers.
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

2. Start the Kafka, Zookeeper, and PostgreSQL services:

```bash
docker-compose up -d
```

3. Verify that the containers are running:

```bash
docker ps
```

4. Start the Spring Boot backend:

```bash
mvn spring-boot:run
```

## 4. Kafka Configuration

### 4.1. Kafka (Kraft)

Kafka is configured to **handle topics** and process messages via **producer** and **consumer**.

- **Kafka Port**: `localhost:9092`

### 4.2. Spring Boot Configuration

Kafka is configured in **`application.yml`** as follows:

```yaml
  kafka:
    bootstrap-servers: localhost:9092
    consumer:
      group-id: trailmetrics-group
      auto-offset-reset: earliest
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.apache.kafka.common.serialization.StringDeserializer
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.apache.kafka.common.serialization.StringSerializer
```

This ensures that the **consumer** can connect to Kafka, read messages, and maintain synchronization with the offset.

## 5. Managing Kafka Topics

### 5.1. Creating a New Topic

Kafka topics can be managed via the CLI.

To create a topic manually, run:

```bash
docker exec -it kafka kafka-topics --create --topic test-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

### 5.2. Listing Topics

To list all available topics:

```bash
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

## 6. Producer and Consumer

### 6.1. Sending Messages to Kafka

Kafka allows sending messages via the **Producer**. You can do this manually from the CLI:

```bash
docker exec -it kafka kafka-console-producer --broker-list localhost:9092 --topic test-topic
```

Write a message (e.g., `TestKafkaMessage`) and press **ENTER**.

### 6.2. Reading Messages from Kafka

To read messages from a topic (e.g., `test-topic`):

```bash
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic test-topic --from-beginning
```

## 7. Common Issues and Solutions

### 7.1. Timeout and Connection Issues
If Kafka fails to connect, check:
- **Listener configuration** in `docker-compose.yml`.
- **Correct connection between consumer and Kafka**.

### 7.2. Consumer Errors
Ensure that the **consumer group** is properly registered and connected:

```bash
docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group trailmetrics-group-new
```
