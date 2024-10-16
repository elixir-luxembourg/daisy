# Database Backup and Restore Script

## Overview

This manual describes steps to perform for backup creation and its restoration.

## Key Functions

- **Backup**: Creates a timestamped `tar.gz` archive of the PostgreSQL database and Django media files.
- **Restore**: Restores from a specified `tar.gz` backup archive.

## Docker Compose Integration

The `backup` service in `docker-compose.yaml` manages backup and restore using the `scripts/db.sh` script.

### Configuration

All variables can be set in the [environment file](.env.template). These include variables necessary for connection to the database, path to local folder where the backup is created and setup of cron tasks for backup.

- **Volumes**:
  - `${BACKUP_VOLUME:-../backups}:/backups`
  - `.:/code`

### Operations

#### Manual Backup

Create a manual backup:

```bash
docker compose exec backup sh /code/scripts/db.sh backup
```

- **Output**: `backup_<timestamp>.tar.gz` in the `BACKUP_DIR` (`../backups` by default).

## Scheduled Backup with Cron

To schedule the backup script to run automatically at a specific time using cron, add the following line to your crontab:

1. Ensure the destination location for backups in `.env` file (`BACKUP_VOLUME` variable)

2. Open the crontab editor:

    ```bash
    crontab -e
    ```

3. Add the cron job entry (for example, to run the backup at 1 AM daily) with path to the backup script:

    ```bash
    0 1 * * * <path-to-project-root>/scripts/backup_script.sh
    ```

4. Check if the cron job is added:

    ```bash
    crontab -l
    ```

## Restore Backup

Restore from a specific backup file:

```bash
docker compose exec backup sh /code/scripts/db.sh restore ../backups/backup_<timestamp>.tar.gz
docker compose run web python manage.py rebuild_index --noinput
```

- Replace `../backups/backup_<timestamp>.tar.gz` with the actual file path.

## List Cron Jobs

View the automatic backup schedule:

```bash
docker compose exec backup crontab -l
```

## List Backup Contents

View contents of a backup archive:

```bash
tar -ztvf ../backups/backup_<timestamp>.tar.gz
```

## Restore Legacy Backup

To restore backup created before version 1.8.1 on newer versions with docker deployment, execute the `legacy_restore.sh` script inside the running container

```bash
# Copy the legacy backup file to the backup container
docker cp ../daisy_prod.tar.gz $(docker compose ps -q backup):/code/daisy_prod.tar.gz

# Execute the legacy_restore.sh script inside the running container
docker compose exec backup /bin/sh -c "sh /code/scripts/legacy_restore.sh /code/daisy_prod.tar.gz && rm /code/daisy_prod.tar.gz"
docker compose run web python manage.py rebuild_index --noinput

# you may also need to run migrate if you have new migration after this backup was created
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic

```

Replace `../daisy_prod.tar.gz` with the actual path to legacy backup file.

### Updating Django Settings to support Docker Compose

After the restore script. you need to change settings_local.py to work with Docker Compose, follow these key changes:

1. **Database Settings:**
   - Change `HOST` from `'localhost'` to the service name defined in Docker (`'db'`):
   ```python
   'HOST': 'db',
   ```

2. **Haystack Solr Configuration:**
   - Change Solr URL and Admin URL to use the Docker service name (`'solr'`):
   ```python
   'URL': 'http://solr:8983/solr/daisy',
   'ADMIN_URL': 'http://solr:8983/solr/admin/cores',
   ```

3. **Static Files:**
   - Update `STATIC_ROOT` to a directory accessible by Docker containers:
   ```python
   STATIC_ROOT = "/static/"
   ```

4. **Allowed Hosts:**
   - Ensure you update the `ALLOWED_HOSTS` to include the IP addresses or domains used by your Docker environment:
   ```python
   ALLOWED_HOSTS = ['IP addresses', 'daisy domain here']
   ```

By making these adjustments,  daisy should now work seamlessly with Docker Compose.
