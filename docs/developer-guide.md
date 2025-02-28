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

To build the images

```sh
docker-compose --build
```

To start and stop a single container (es. auth-service)

```sh
docker stop auth-service
docker start auth-service
```

To enter the container folders (es. read auth-service logs)

```sh
docker exec -it auth-service cat /app/logs/app.logs
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

# Python run app

```sh
python app.py
```
