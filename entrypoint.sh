#!/bin/sh
# Runs collectstatic to populate the bind-mounted staticfiles directory
# before starting the application server.
set -e
python manage.py collectstatic --noinput
exec "$@"
