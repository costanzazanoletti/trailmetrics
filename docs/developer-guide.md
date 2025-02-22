## Database Backup & Restore

To create a PostgreSQL dump from Docker:

```sh
docker exec -t <postgres_container_id> pg_dump -U <db_user> -d <db_name> > dump_file_name.sql
```

## Docker

```sh
docker-compose up -d
```

## AKHQ UI for Kafka

Access via browser http://localhost:9080
