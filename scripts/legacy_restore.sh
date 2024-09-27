#!/bin/sh

# Exit immediately if a command exits with a non-zero status and treat unset variables as errors
set -eu

# Configuration
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-daisy}"
DB_USER="${DB_USER:-daisy}"
DB_PASSWORD="${DB_PASSWORD:-daisy}"
MEDIA_DIR="${MEDIA_DIR:-/code/documents}"
SHOW_DB_LOGS="${SHOW_DB_LOGS:-true}"

# Check if TAR_FILE argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 path_to_daisy_backup_tar.gz" >&2
    exit 1
fi

TAR_FILE=$1

# Initialize variables before defining cleanup
EXTRACT_LIST=""

# Create a temporary directory for extraction
TEMP_DIR=$(mktemp -d /tmp/restore_temp.XXXXXX)

# Function to clean up temporary directories on exit
cleanup() {
    rm -rf "$TEMP_DIR" "$EXTRACT_LIST"
}
trap cleanup EXIT

# Ensure TEMP_DIR was created successfully
if [ ! -d "$TEMP_DIR" ]; then
    echo "ERROR: Failed to create temporary directory." >&2
    exit 1
fi

echo "Step 1: Starting restoration process..."

echo "Step 2: Searching for daisy_dump.sql, documents directory, and settings_local.py in the archive..."

# Initialize search result variables
SQL_DUMP_PATH=""
DOCUMENTS_DIR_PATH=""
SETTINGS_LOCAL_PATH=""

# Search for daisy_dump.sql
SQL_DUMP_PATH=$(tar -tzf "$TAR_FILE" | grep "/daisy_dump\.sql$" | head -n 1 || true)

# Search for documents directory (any depth) excluding those under 'templates'
DOCUMENTS_DIR_PATH=$(tar -tzf "$TAR_FILE" | grep "/documents/$" | grep -v "/templates/" | head -n 1 || true)

# Search for settings_local.py (optional)
SETTINGS_LOCAL_PATH=$(tar -tzf "$TAR_FILE" | grep "/settings_local\.py$" | head -n 1 || true)

# Check if SQL dump is found
if [ -z "$SQL_DUMP_PATH" ]; then
    echo "ERROR: SQL dump 'daisy_dump.sql' not found in the archive." >&2
    # Proceeding without exiting to allow extraction of other files
fi

# Check if documents directory is found
if [ -z "$DOCUMENTS_DIR_PATH" ]; then
    echo "WARNING: Documents directory not found in the archive or it is under 'templates/'." >&2
fi

# settings_local.py is optional
if [ -z "$SETTINGS_LOCAL_PATH" ]; then
    echo "INFO: settings_local.py not found in the archive. Continuing without it." >&2
fi

# Prepare list of paths to extract
EXTRACT_LIST=$(mktemp /tmp/extract_list.XXXXXX)

# Add found paths to the extract list if they exist
if [ -n "$SQL_DUMP_PATH" ]; then
    echo "$SQL_DUMP_PATH" >> "$EXTRACT_LIST"
fi

if [ -n "$DOCUMENTS_DIR_PATH" ]; then
    echo "$DOCUMENTS_DIR_PATH" >> "$EXTRACT_LIST"
fi

if [ -n "$SETTINGS_LOCAL_PATH" ]; then
    echo "$SETTINGS_LOCAL_PATH" >> "$EXTRACT_LIST"
fi

# Check if EXTRACT_LIST has entries
if [ ! -s "$EXTRACT_LIST" ]; then
    echo "ERROR: No files or directories to extract. Exiting." >&2
    exit 1
fi

echo "Step 3: Extracting the necessary files and directories..."
if ! tar -xzf "$TAR_FILE" -C "$TEMP_DIR" -T "$EXTRACT_LIST" 2>&1; then
    echo "ERROR: Failed to extract necessary files from the backup archive." >&2
    exit 1
fi

echo "Step 4: Verifying extracted contents..."
SQL_DUMP=$(find "$TEMP_DIR" -type f -name "daisy_dump.sql" | head -n 1 || true)
DOCUMENTS_DIR=$(find "$TEMP_DIR" -type d -name "documents" | grep -v "/templates/" | head -n 1 || true)
SETTINGS_LOCAL=$(find "$TEMP_DIR" -type f -name "settings_local.py" | head -n 1 || true)

echo "Step 5: Dropping existing database..."
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

echo "Step 6: Creating new database..."
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

echo "Step 7: Restoring PostgreSQL database from SQL dump..."
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

echo "Step 8: Restoring Django media files..."
if [ -n "$DOCUMENTS_DIR" ] && [ -d "$DOCUMENTS_DIR" ]; then
    rm -rf "${MEDIA_DIR:?}/"*
    if ! cp -R "${DOCUMENTS_DIR}/." "${MEDIA_DIR}/"; then
        echo "ERROR: Media files restoration failed" >&2
        rm -rf "$TEMP_DIR"
        exit 1
    fi
else
    echo "WARNING: No media backup found in the archive. Skipping media restoration."
fi

echo "Step 9: Restoring settings_local.py..."
if [ -n "$SETTINGS_LOCAL" ] && [ -f "$SETTINGS_LOCAL" ]; then
    if [ -f "/code/elixir_daisy/settings_local.py" ]; then
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

echo "Step 10: Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

echo "Step 11: Restoration completed successfully."
