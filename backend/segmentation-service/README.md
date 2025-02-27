# Segmentation Service

## 📖 Overview

The **Segmentation Service** is a microservice responsible for processing activity data, segmenting the route based on elevation changes, and publishing the results to Kafka. This service is part of the **TRAILMETRICS** project and interacts with PostgreSQL, Kafka, and external APIs.

## 🛠 Setup

### 1️⃣ Install Dependencies

The service runs on **Python 3.10+**. First, create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2️⃣ Create the `.env` File

The `.env` file contains environment variables required for the service. **Do not commit this file to Git!** Create a `.env` file in the root of `segmentation-service/` with:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/trailmetrics
KAFKA_BROKER=broker:29092
FLASK_ENV=development
```

### 3️⃣ Running Locally

After setting up the environment, start the service with:

```bash
python app.py
```

The service should be accessible at **http://127.0.0.1:5001/**.

## 🐳 Running with Docker

To run the service inside a Docker container:

```bash
docker-compose up --build segmentation-service
```

If you made changes to `requirements.txt` or `Dockerfile`, rebuild:

```bash
docker-compose up --build -d
```

## ✅ Running Tests

To test the service, activate the virtual environment and run:

```bash
pytest tests/
```

For detailed testing procedures, refer to the **[Developer Guide](../../docs/developer-guide.md)**.

## 🔗 More Information

For a complete setup of **TRAILMETRICS**, check the [Developer Guide](../../docs/developer-guide.md).
