#!/bin/bash

# Stop services that should not run during the backup
docker compose stop nginx flower worker beat web mq solr

# Run the backup script inside the backup container
docker compose exec backup sh /code/scripts/db.sh backup

# Start the services back up after the backup is complete
docker compose up -d solr mq web worker beat flower nginx
