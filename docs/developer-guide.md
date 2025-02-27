## Database Backup & Restore

To create a PostgreSQL dump from Docker:

```sh
docker exec -t <postgres_container_id> pg_dump -U <db_user> -d <db_name> > dump_file_name.sql
```

## Docker

To run in detached mode

```sh
docker-compose up -d
```

To shut it down

```sh
docker-compose down
```

To build it when changing python requirements.txt or Dockerfile

```sh
docker-compose --build
```

## AKHQ UI for Kafka

Access via browser http://localhost:9080

# Python run tests

If tests is the name of the tests folder:

```sh
pytest tests/
```

To show the output in terminal

```sh
pytest -s tests/
```
