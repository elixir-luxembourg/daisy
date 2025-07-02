#!/bin/bash

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-../backups}"     # Directory to store backups
DB_HOST="${DB_HOST:-db}"                   # PostgreSQL host
DB_PORT="${DB_PORT:-5432}"                 # PostgreSQL port
DB_NAME="${DB_NAME:-daisy}"                # PostgreSQL database name
DB_USER="${DB_USER:-daisy}"                # PostgreSQL user
DB_PASSWORD="${DB_PASSWORD:-daisy}"        # PostgreSQL password
MEDIA_DIR="${MEDIA_DIR:-/code/documents}"  # Django media directory
BACKUP_VOLUME="${BACKUP_VOLUME:-../backups}"  # Backup volume

if [ "${BACKUP_DIR}" == "../backups" ] && [ ! -d "${BACKUP_DIR}" ]; then
    mkdir -p "${BACKUP_DIR}"
fi

# Function to perform backup
backup() {
    local timestamp
    timestamp=$(date +%Y-%m-%d_%H-%M-%S)
    local backup_file="${BACKUP_DIR}/backup_${timestamp}.tar.gz"
    local temp_backup_dir="${BACKUP_DIR}/temp_${timestamp}"

    echo "Starting backup..."

    # Create temporary backup directory
    mkdir -p "${temp_backup_dir}"

    # Backup database as SQL dump
    echo "Backing up PostgreSQL database..."
    if ! PGPASSWORD="${DB_PASSWORD}" pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -F p -f "${temp_backup_dir}/db_backup.sql"; then
        echo "ERROR: Database backup failed" >&2
        rm -rf "${temp_backup_dir}"
        exit 1
    fi

    # Backup media files
    echo "Backing up Django media files..."
    if [ -d "${MEDIA_DIR}" ]; then
        if ! cp -R "${MEDIA_DIR}" "${temp_backup_dir}/documents"; then
            echo "ERROR: Media files backup failed" >&2
            rm -rf "${temp_backup_dir}"
            exit 1
        fi
    else
        echo "WARNING: Media directory not found. Skipping media backup."
    fi

    # Create tar.gz archive of the backups
    echo "Creating tar.gz archive..."
    if ! tar -czf "${backup_file}" -C "${BACKUP_DIR}" "temp_${timestamp}"; then
        echo "ERROR: Archive creation failed" >&2
        rm -rf "${temp_backup_dir}"
        exit 1
    fi

    # Remove temporary backup directory
    rm -rf "${temp_backup_dir}"

    echo "Backup completed successfully: ${BACKUP_VOLUME}/backup_${timestamp}.tar.gz"
}

# Function to perform restore
restore() {
    if [ $# -ne 1 ]; then
        echo "Usage: $0 restore <backup_file.tar.gz>" >&2
        exit 1
    fi

    local backup_file="$1"
    local tmp_restore_dir="${BACKUP_DIR}/restore_temp"

    if [ ! -f "${backup_file}" ]; then
        echo "ERROR: Backup file not found: ${backup_file}" >&2
        exit 1
    fi

    echo "Starting restoration..."

    # Drop the existing database
    echo "Dropping existing database..."
    if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};"; then
        echo "ERROR: Failed to drop existing database" >&2
        exit 1
    fi

    # Create a new database
    echo "Creating new database..."
    if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME};"; then
        echo "ERROR: Failed to create new database" >&2
        exit 1
    fi

    # Extract the backup archive
    mkdir -p "${tmp_restore_dir}"
    if ! tar -xzf "${backup_file}" -C "${tmp_restore_dir}"; then
        echo "ERROR: Failed to extract backup archive" >&2
        rm -rf "${tmp_restore_dir}"
        exit 1
    fi

    # Identify the extracted directory (e.g., temp_2023-10-05_12-00-00)
    local extracted_dir
    extracted_dir=$(ls "${tmp_restore_dir}")

    # Restore PostgreSQL database from SQL dump
    echo "Restoring PostgreSQL database..."
    if ! PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -f "${tmp_restore_dir}/${extracted_dir}/db_backup.sql"; then
        echo "ERROR: Database restoration failed" >&2
        rm -rf "${tmp_restore_dir}"
        exit 1
    fi

    # Restore media files
    echo "Restoring Django media files..."
    if [ -d "${tmp_restore_dir}/${extracted_dir}/documents" ]; then
        if [ ! -d "${MEDIA_DIR}" ]; then
            echo "Creating media directory: ${MEDIA_DIR}"
            mkdir -p "${MEDIA_DIR}"
        fi
        rm -rf "${MEDIA_DIR:?}/"*
        if ! cp -R "${tmp_restore_dir}/${extracted_dir}/documents/"* "${MEDIA_DIR}/"; then
            echo "ERROR: Media files restoration failed" >&2
            rm -rf "${tmp_restore_dir}"
            exit 1
        fi
    else
        echo "WARNING: No media backup found in the archive. Skipping media restoration."
    fi

    # Remove temporary restoration directory
    rm -rf "${tmp_restore_dir}"

    echo "Restoration completed successfully."
}

# Main script logic
case "$1" in
    backup)
        backup
        ;;
    restore)
        shift
        restore "$@"
        ;;
    *)
        echo "Usage: $0 {backup|restore <backup_file.tar.gz>}" >&2
        exit 1
        ;;
esac
