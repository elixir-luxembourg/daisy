# Database Backup and Restore Script

## Overview
Manage PostgreSQL database backups and Django media files in a Docker environment using `tar.gz` archives.

## Key Functions
- **Backup**: Creates a timestamped `tar.gz` archive of the PostgreSQL database and Django media files.
- **Restore**: Restores from a specified `tar.gz` backup archive.

## Docker Compose Integration
The `backup` service in `docker-compose.yaml` manages backup and restore using the `db.sh` script.

### Configuration

- **Environment Variables**:
  - `DB_HOST` (default: `db`)
  - `DB_PORT` (default: `5432`)
  - `DB_NAME` (default: `daisy`)
  - `DB_USER` (default: `daisy`)
  - `DB_PASSWORD` (default: `daisy`)
  - `BACKUP_DIR` (default: `../backups`)
  - `ENABLE_BACKUPS` (default: `true`)
  - `BACKUP_SCHEDULE` (default: `"0 0 * * *"`)

- **Volumes**:
  - `${BACKUP_VOLUME:-../backups}:/backups`
  - `.:/code`

### Operations

#### Enable Automatic Backups
To ensure automatic backups are enabled, set `ENABLE_BACKUPS=true` (enabled by default):

To checkout if the cron is added 

```bash
docker compose exec backup crontab -l
```

```bash
ENABLE_BACKUPS=true docker compose up -d backup
```
This will configure automatic backups based on the `BACKUP_SCHEDULE`.

#### Automatic Backups
- Enabled by default (`ENABLE_BACKUPS=true`).
- Schedule defined by `BACKUP_SCHEDULE` (cron format).

To disable automatic backups:
```bash
ENABLE_BACKUPS=false docker compose up -d backup
```

To checkout if the cron was removed 

```bash
docker compose exec backup crontab -l
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
Execute the `legacy_restore.sh` script inside the running container

```bash
# Copy the legacy backup file to the backup container
docker cp ../daisy.tar.gz $(docker compose ps -q backup):/code/daisy.tar.gz

# Execute the legacy_restore.sh script inside the running container
docker compose exec backup /bin/sh -c "sh /code/legacy_restore.sh /code/daisy.tar.gz && rm /code/daisy.tar.gz"
docker compose run web python manage.py rebuild_index --noinput
```
Replace `../daisy.tar.gz` with the actual path to legacy backup file.


#### Reindex Solr

To rebuild the Solr search index after a restore operation:

```bash
docker compose run web python manage.py rebuild_index --noinput
```