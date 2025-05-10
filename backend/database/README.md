# Database Setup Guide

## Overview

This directory contains SQL scripts to initialize and configure the PostgreSQL database for the TrailMetrics application. It includes creation of users, tables, and optional seed data. All initialization is performed automatically via Docker when the system starts.

## Directory Structure

```
backend/database/
├── init/                      # Executed on Postgres container startup
│   ├── 01_create_database.sql
│   ├── 02_create_schema.sql
│   └── (generated) 03_create_users.sql
├── templates/                # Contains 03_create_users.template.sql for env-based user injection
├── entrypoint.sh             # Custom entrypoint for PostgreSQL to generate SQL from template
├── .env                      # Defines sensitive database user credentials
├── .env.example              # Public reference of required env vars
├── Dockerfile.postgres       # Extends base postgres image with envsubst support
└── README.md                 # This file
```

## Automatic Initialization (Docker)

PostgreSQL initialization is handled automatically at container startup using Docker volumes. Ensure the following is configured in `docker-compose.yml`:

```yaml
services:
  postgres:
    build:
      context: ./backend/database
      dockerfile: Dockerfile.postgres
    entrypoint: ["/entrypoint.sh"]
    volumes:
      - ./backend/database/init:/docker-entrypoint-initdb.d
      - ./backend/database/templates:/templates:ro
      - ./backend/database/entrypoint.sh:/entrypoint.sh:ro
    env_file:
      - ./backend/database/.env
```

## Environment Variables

Configuration variables must be defined in a `.env` file. An example is available at `.env.example`.

These are used at container runtime to inject database usernames and passwords into the initialization script.

## RSA Key Notes

This service does not handle key management, but services like `auth-service` expect keys stored externally. Database secrets are injected at container startup only.

## Manual Execution (Development)

If needed, SQL files can be run manually using `psql`:

```bash
psql -U postgres -f backend/database/init/01_create_database.sql
```
