# Database Setup Guide

## Overview
This directory contains SQL scripts to initialize and configure the PostgreSQL databases for the TrailMetrics application. The setup includes separate databases for different microservices, user management, and schema initialization.

## Structure
```
/database/
│── init/
│   ├── 01_create_databases.sql  # Creates the databases
│   ├── 02_create_users.sql      # Creates users and assigns privileges
│   ├── 03_create_tables.sql     # Defines the table structures
│   ├── 04_seed_data.sql         # Inserts initial test data (optional)
│── migrations/                   # (For Flyway or Liquibase migrations)
│── README.md                     # Documentation for database setup
```

## PostgreSQL Database Setup

### 1. Creating Databases
To create the required databases, execute the following command:
```sh
psql -U postgres -f init/01_create_databases.sql
```
This will create:
- `activity_service`: Stores activity data and user preferences.
- `analytics_service`: Stores computed analytics and segments.

### 2. Creating Users
Execute:
```sh
psql -U postgres -f init/02_create_users.sql
```
This creates:
- `activity_user`: Access to `activity_service`.
- `analytics_user`: Access to `analytics_service`.

### 3. Creating Tables
Execute:
```sh
psql -U postgres -f init/03_create_tables.sql
```
This will set up the necessary tables within each database.

### 4. Seeding Data (Optional)
If you want to populate the database with test data:
```sh
psql -U postgres -f init/04_seed_data.sql
```

## Using Docker for Database Initialization
If running PostgreSQL in Docker, mount the `init` directory so scripts run automatically:
```yaml
services:
  postgres:
    image: postgres:latest
    container_name: postgres
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: mypassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d
```
This ensures PostgreSQL runs the scripts during container startup.

## Connecting to the Database
Use `psql` to connect manually:
```sh
psql -U postgres -d activity_service
psql -U postgres -d analytics_service
```
Or, for remote connections:
```sh
psql -h <host> -U <user> -d <database>
```

## Notes
- Ensure PostgreSQL is running before executing scripts.
- Modify `.env` files to reflect the correct database credentials for each service.
- For production, ensure proper access controls are configured.

## Troubleshooting
If errors occur, check:
- PostgreSQL logs (`docker logs postgres` if running in Docker).
- Connection details and user permissions.
- If any previous conflicting schemas exist (`\dt` in `psql`).

