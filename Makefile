# TrailMetrics - Makefile

# Run all services
up:
	docker compose up -d

# Stop and remove all containers and volumes
down:
	docker compose down -v

# Rebuild all images
build:
	docker compose build

# Full restart with cleanup
rebuild:
	docker compose down -v
	docker compose build
	docker compose up -d

# View logs for a specific service (use: make logs s=auth-service)
logs:
	docker compose logs -f $(s)

# Open a shell in a running container (use: make shell s=efficiency-service)
shell:
	docker compose exec $(s) sh
