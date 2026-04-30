#!/bin/bash

# Stop services that should not run during the backup.
docker compose stop worker beat web

# Run the backup script inside the backup container
docker compose exec backup sh /code/scripts/db.sh backup

# Start the services back up after the backup is complete
docker compose up -d web worker beat

# Ensure nginx re-resolves service names in case container IPs changed
docker compose exec nginx nginx -s reload
