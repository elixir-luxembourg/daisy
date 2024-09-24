# Database Backup and Restore Script

## Overview

This manual describes steps to perform for backup creation and its restoration.

## Key Functions

- **Backup**: Creates a timestamped `tar.gz` archive of the PostgreSQL database and Django media files.
- **Restore**: Restores from a specified `tar.gz` backup archive.

## Docker Compose Integration

The `backup` service in `docker-compose.yaml` manages backup and restore using the `db.sh` script.

### Configuration

All variables can be set in the [environment file](.env.template). These include variables necessary for connection to the database, path to local folder where the backup is created and setup of cron tasks for backup.

- **Volumes**:
  - `${BACKUP_VOLUME:-../backups}:/backups`
  - `.:/code`

### Operations

#### Enable Automatic Backups

To ensure automatic backups are enabled, set `ENABLE_BACKUPS=true` (enabled by default):


```bash
ENABLE_BACKUPS=true docker compose up -d backup
```

This will configure automatic backups based on the `BACKUP_SCHEDULE`.

To disable automatic backups:

```bash
ENABLE_BACKUPS=false docker compose up -d backup
```

#### Manual Backup

Create a manual backup:

```bash
docker compose exec backup sh /code/db.sh backup
```

- **Output**: `backup_<timestamp>.tar.gz` in the `BACKUP_DIR` (`../backups` by default).

#### Restore Backup

Restore from a specific backup file:

```bash
docker compose exec backup sh /code/db.sh restore ../backups/backup_<timestamp>.tar.gz
docker compose run web python manage.py rebuild_index --noinput
```

- Replace `../backups/backup_<timestamp>.tar.gz` with the actual file path.

#### List Cron Jobs

View the automatic backup schedule:

```bash
docker compose exec backup crontab -l
```

#### List Backup Contents

View contents of a backup archive:

```bash
tar -ztvf ../backups/backup_<timestamp>.tar.gz
```

#### Restore Legacy Backup

To restore backup created before version 1.8.1 on newer versions with docker deployment, execute the `legacy_restore.sh` script inside the running container

```bash
# Copy the legacy backup file to the backup container
docker cp ../daisy.tar.gz $(docker compose ps -q backup):/code/daisy_prod.tar.gz

# Execute the legacy_restore.sh script inside the running container
docker compose exec backup /bin/sh -c "sh /code/legacy_restore.sh /code/daisy_prod.tar.gz && rm /code/daisy_prod.tar.gz"
docker compose run web python manage.py rebuild_index --noinput
```

Replace `../daisy.tar.gz` with the actual path to legacy backup file.

#### Reindex Solr

To rebuild the Solr search index after a restore operation:

```bash
docker compose run web python manage.py rebuild_index --noinput
```
