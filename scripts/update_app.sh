#!/bin/bash
set -e

APP_VERSION="${1:-${APP_VERSION:-develop}}"
APP_IMAGE="ghcr.io/elixir-luxembourg/daisy:${APP_VERSION}"

echo "=== Updating Daisy (image: ${APP_IMAGE}) ==="

# image must exist before touching anything
if ! docker manifest inspect "${APP_IMAGE}" >/dev/null 2>&1; then
    echo "Error: image '${APP_IMAGE}' not found in registry." >&2
    exit 1
fi

git pull

# Update APP_IMAGE in .env
if [ -f .env ]; then
    if grep -q '^APP_IMAGE=' .env; then
        sed -i.bak "s|^APP_IMAGE=.*|APP_IMAGE=${APP_IMAGE}|g" .env && rm .env.bak
    else
        echo "" >> .env && echo "APP_IMAGE=${APP_IMAGE}" >> .env
    fi
else
    echo "APP_IMAGE=${APP_IMAGE}" > .env
fi

docker compose pull web worker beat

docker compose up -d --no-deps web worker beat
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py rebuild_index --noinput
docker compose exec web python manage.py import_users \
    || echo "Warning: import_users failed (LDAP/AD may be unavailable)." >&2

# rm the images the update replaced: untagged leftovers, then older daisy tags
docker image prune -f
docker images --format '{{.Repository}}:{{.Tag}}' ghcr.io/elixir-luxembourg/daisy \
    | grep -vx "${APP_IMAGE}" \
    | xargs -r docker rmi >/dev/null 2>&1 || true

echo "Done!"
