#!/bin/sh

# Ensure the backup script is executable
chmod +x /code/db.sh

# Check if backups are enabled
if [ "$ENABLE_BACKUPS" = "true" ]; then
  # Install necessary packages
  apk add --no-cache bash curl tar gzip postgresql-client openrc cronie

  # Set up the crontab entry
  echo "$BACKUP_SCHEDULE /code/db.sh backup" | tr -d '"' > /etc/crontabs/root

  # Print the crontab contents for debugging
  echo "Crontab contents:"
  cat /etc/crontabs/root

  # Start the cron daemon
  crond -f
else
  echo "Backups are disabled. Set ENABLE_BACKUPS=true to enable."
  tail -f /dev/null
fi