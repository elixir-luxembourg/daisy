#!/bin/bash

set -euo pipefail

# Configuration
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-daisy}"
DB_USER="${DB_USER:-daisy}"
DB_PASSWORD="${DB_PASSWORD:-daisy}"
MEDIA_DIR="${MEDIA_DIR:-/code/documents}"
SHOW_DB_LOGS="${SHOW_DB_LOGS:-true}"

if [ $# -ne 1 ]; then
    echo "Usage: $0 path_to_daisy_backup_tar.gz" >&2
    exit 1
fi

TAR_FILE=$1
TEMP_DIR=$(mktemp -d)

echo "Step 1: Starting restoration process..."

echo "Step 2: Extracting backup archive..."
if ! tar -xzf "$TAR_FILE" -C "$TEMP_DIR" > /dev/null 2>&1; then
    echo "ERROR: Failed to extract backup archive" >&2
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Step 3: Locating SQL dump, documents directory, and settings_local.py..."
SQL_DUMP=$(find "$TEMP_DIR" -name "daisy_dump.sql")
DOCUMENTS_DIR=$(find "$TEMP_DIR" -type d -name "documents" ! -path "*/templates/*" | head -n 1)
SETTINGS_LOCAL=$(find "$TEMP_DIR" -type f -name "settings_local.py" | head -n 1)

echo "Step 4: Verifying extracted contents..."
echo "  - SQL dump found: $([ -n "$SQL_DUMP" ] && echo "Yes" || echo "No")"
echo "  - Documents directory found: $([ -n "$DOCUMENTS_DIR" ] && echo "Yes" || echo "No")"
echo "  - settings_local.py found: $([ -n "$SETTINGS_LOCAL" ] && echo "Yes" || echo "No")"

if [ -z "$SQL_DUMP" ]; then
    echo "ERROR: Could not find daisy_dump.sql in the archive" >&2
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Step 5: Extraction successful."
echo "  - SQL dump location: $SQL_DUMP"
echo "  - Documents location: $DOCUMENTS_DIR"
echo "  - settings_local.py location: $SETTINGS_LOCAL"

echo "Step 6: Dropping existing database..."
if [ "$SHOW_DB_LOGS" = "true" ]; then
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"
else
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};" > /dev/null 2>&1
fi

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to drop existing database" >&2
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Step 7: Creating new database..."
if [ "$SHOW_DB_LOGS" = "true" ]; then
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME};"
else
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME};" > /dev/null 2>&1
fi

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create new database" >&2
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Step 8: Restoring PostgreSQL database from SQL dump..."
if [ "$SHOW_DB_LOGS" = "true" ]; then
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -f "${SQL_DUMP}"
else
    PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -f "${SQL_DUMP}" > /dev/null 2>&1
fi

if [ $? -ne 0 ]; then
    echo "ERROR: Database restoration failed" >&2
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "Step 9: Restoring Django media files..."
if [ -n "$DOCUMENTS_DIR" ] && [ -d "$DOCUMENTS_DIR" ]; then
    echo "  - Copying files from $DOCUMENTS_DIR to $MEDIA_DIR"
    rm -rf "${MEDIA_DIR:?}/"*
    if ! cp -R "${DOCUMENTS_DIR}/." "${MEDIA_DIR}/"; then
        echo "ERROR: Media files restoration failed" >&2
        rm -rf "$TEMP_DIR"
        exit 1
    fi
else
    echo "WARNING: No media backup found in the archive. Skipping media restoration."
fi

echo "Step 10: Restoring settings_local.py..."
if [ -n "$SETTINGS_LOCAL" ] && [ -f "$SETTINGS_LOCAL" ]; then
    echo "  - Copying settings_local.py to /code/elixir_daisy/"
    if [ -f "/code/elixir_daisy/settings_local.py" ]; then
        echo "  - Existing settings_local.py found. Replacing it."
        if ! cp -f "$SETTINGS_LOCAL" "/code/elixir_daisy/settings_local.py"; then
            echo "ERROR: Failed to replace existing settings_local.py" >&2
            rm -rf "$TEMP_DIR"
            exit 1
        fi
    else
        if ! cp "$SETTINGS_LOCAL" "/code/elixir_daisy/settings_local.py"; then
            echo "ERROR: Failed to restore settings_local.py" >&2
            rm -rf "$TEMP_DIR"
            exit 1
        fi
    fi
else
    echo "WARNING: settings_local.py not found in the archive. Skipping restoration."
fi

echo "Step 11: Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo "Step 12: Restoration completed successfully."
