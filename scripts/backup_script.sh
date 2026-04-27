#!/bin/bash

# Stop services that should not run during the backup.
# Keep nginx running so static content remains reachable while the app is paused.
docker compose stop flower worker beat web mq solr

# Run the backup script inside the backup container
docker compose exec backup sh /code/scripts/db.sh backup

# Start the services back up after the backup is complete
docker compose up -d solr mq web worker beat flower
