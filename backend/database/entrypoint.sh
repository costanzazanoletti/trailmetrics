#!/bin/bash
set -e

TEMPLATE_FILE="/templates/03_create_users.template.sql"
OUTPUT_FILE="/docker-entrypoint-initdb.d/03_create_users.sql"

if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "ERROR: Template file not found: $TEMPLATE_FILE"
  exit 1
fi

echo "Generating SQL file from template..."
envsubst < "$TEMPLATE_FILE" > "$OUTPUT_FILE"

echo "Final SQL file content:"
cat "$OUTPUT_FILE"

# Avvia PostgreSQL
exec docker-entrypoint.sh postgres
