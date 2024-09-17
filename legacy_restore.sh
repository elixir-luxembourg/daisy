#!/bin/bash

set -euo pipefail

# Configuration
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-daisy}"
DB_USER="${DB_USER:-daisy}"
DB_PASSWORD="${DB_PASSWORD:-daisy}"
MEDIA_DIR="${MEDIA_DIR:-/code/documents}"

if [ $# -ne 1 ]; then
    echo "Usage: $0 path_to_daisy_backup_tar.gz" >&2
    exit 1
fi

TAR_FILE=$1
TEMP_DIR=$(mktemp -d)

echo "Starting restoration..."

# Extract the backup archive
echo "Extracting files..."
if ! tar -xzvf "$TAR_FILE" -C "$TEMP_DIR" \
    --strip-components=2 \
    home/daisy/daisy_dump.sql \
    home/daisy/daisy/documents; then
    echo "ERROR: Failed to extract backup archive" >&2
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Extraction successful."
echo "SQL dump: $TEMP_DIR/daisy_dump.sql"
echo "Documents: $TEMP_DIR/daisy/documents"

# Drop the existing database
echo "Dropping existing database..."
if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"; then
    echo "ERROR: Failed to drop existing database" >&2
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Create a new database
echo "Creating new database..."
if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME};"; then
    echo "ERROR: Failed to create new database" >&2
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Restore PostgreSQL database from SQL dump
echo "Restoring PostgreSQL database..."
if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -f "${TEMP_DIR}/daisy_dump.sql"; then
    echo "ERROR: Database restoration failed" >&2
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Restore media files
echo "Restoring Django media files..."
if [ -d "${TEMP_DIR}/daisy/documents" ]; then
    rm -rf "${MEDIA_DIR:?}/"*
    if ! cp -R "${TEMP_DIR}/daisy/documents/"* "${MEDIA_DIR}/"; then
        echo "ERROR: Media files restoration failed" >&2
        rm -rf "$TEMP_DIR"
        exit 1
    fi
else
    echo "WARNING: No media backup found in the archive. Skipping media restoration."
fi

# Remove temporary directory
rm -rf "$TEMP_DIR"

echo "Restoration completed successfully."
