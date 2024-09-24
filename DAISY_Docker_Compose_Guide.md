# Daisy Project Setup Guide

This guide provides concise instructions for setting up and running the Daisy project using Docker Compose. It includes commands for managing the Django application and other services within the project.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [Clone the Repository](#clone-the-repository)
  - [Environment Variables](#environment-variables)
- [Running the Project](#running-the-project)
  - [Build and Start Services](#build-and-start-services)
  - [Initialize the Database](#initialize-the-database)
  - [Build the Solr Schema](#build-the-solr-schema)
  - [Compile and Deploy Static Files](#compile-and-deploy-static-files)
  - [Load Initial Data into the Database](#load-initial-data-into-the-database)
  - [Load Demo Data (Optional)](#load-demo-data-optional)
  - [Build the Search Index](#build-the-search-index)
  - [Access the Application](#access-the-application)
- [Managing the Django Application](#managing-the-django-application)
  - [Access the Web Service](#access-the-web-service)
  - [Run Django Commands](#run-django-commands)
- [Managing Other Services](#managing-other-services)
  - [PostgreSQL Database (`db` Service)](#postgresql-database-db-service)
  - [Solr (`solr` Service)](#solr-solr-service)
  - [RabbitMQ (`mq` Service)](#rabbitmq-mq-service)
  - [Celery Worker (`worker` Service)](#celery-worker-worker-service)
  - [Celery Beat (`beat` Service)](#celery-beat-beat-service)
  - [Flower Monitoring Tool (`flower` Service)](#flower-monitoring-tool-flower-service)
- [Backup and Restore Operations](#backup-and-restore-operations)
  - [Backup Service (`backup`)](#backup-service-backup)
  - [Restore from Backup](#restore-from-backup)
  - [Restore Legacy Backup](#restore-legacy-backup)
- [Importing and Exporting Data](#importing-and-exporting-data)
  - [Import Data](#import-data)
  - [Export Data](#export-data)
- [Updating the Project](#updating-the-project)
  - [Pull Latest Changes](#pull-latest-changes)
  - [Rebuild Services After Code Changes](#rebuild-services-after-code-changes)
  - [Database Backup Before Upgrade](#database-backup-before-upgrade)
  - [Upgrade Steps](#upgrade-steps)
- [Administration](#administration)
- [Settings Reference](#settings-reference)
- [Additional Tips](#additional-tips)
- [Docker Compose Services Overview](#docker-compose-services-overview)
- [Logs and Monitoring](#logs-and-monitoring)
- [Clean Up](#clean-up)

---

## Prerequisites

- **Docker**
- **Docker Compose**

---

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/elixir-luxembourg/daisy.git
cd daisy
```

### Environment Variables

Create a `.env` file in the project root to override default environment variables if necessary.

Example `.env` file:

```env
DB_NAME=daisy
DB_USER=daisy
DB_PASSWORD=daisy
BACKUP_VOLUME=../backups
```

---

## Running the Project

### Build and Start Services

Build and start all services defined in `docker-compose.yaml`:

```bash
docker compose up -d --build
```

### Initialize the Database

Run database migrations:

```bash
docker compose exec web python manage.py migrate
```

### Build the Solr Schema

Build the Solr schema required for full-text search:

```bash
docker compose exec web python manage.py build_solr_schema -c /solr/daisy/conf -r daisy -u default
```

### Compile and Deploy Static Files

The project uses frontend assets that need to be compiled (e.g., with npm), you need to build them and collect static files.

#### Install npm Dependencies

```bash
cd web/static/vendor
npm ci
```

#### Build Frontend Assets

```bash
npm run build
```

#### Collect Static Files

From the project root:

```bash
docker compose exec web python manage.py collectstatic --noinput
```

### Load Initial Data into the Database

Load initial data, such as controlled vocabularies and initial list of institutions and cohorts.

```bash
docker compose exec web bash -c "
    cd core/fixtures/ && \
    wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/edda.json && \
    wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hpo.json && \
    wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hdo.json && \
    wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hgnc.json
"
docker compose exec web python manage.py load_initial_data
```

**Note:** This step can take several minutes to complete.

### Load Demo Data (Optional)

To load demo data, including mock datasets, projects, and a demo admin account:

```bash
docker compose exec web python manage.py load_demo_data
```

### Build the Search Index

After loading data, build the search index for Solr:

```bash
docker compose exec web python manage.py rebuild_index --noinput
```

### Access the Application

The application should now be accessible at:

- **HTTP:** `http://localhost/`
- **HTTPS:** `https://localhost/`

If you loaded the demo data, you can log in with the demo credentials provided during the demo data setup.

---

## Managing the Django Application

### Access the Web Service

Shell into the `web` container:

```bash
docker compose exec web /bin/bash
```

### Run Django Commands

Run Django management commands using the `web` service.

#### Make Migrations

```bash
docker compose exec web python manage.py makemigrations
```

#### Apply Migrations

```bash
docker compose exec web python manage.py migrate
```

#### Create Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

#### Collect Static Files

```bash
docker compose exec web python manage.py collectstatic --noinput
```

#### Rebuild Solr Index

```bash
docker compose exec web python manage.py rebuild_index --noinput
```

---

## Managing Other Services

### PostgreSQL Database (`db` Service)

#### Access the Database Shell

```bash
docker compose exec db psql -U daisy -d
```

#### Execute SQL Commands

Run SQL commands directly:

```bash
docker compose exec db psql -U daisy -d daisy -c "SELECT * FROM user;"
```

### Solr (`solr` Service)

#### Access Solr Admin Interface

Solr runs on port `8983`. Access it via:

```
http://localhost:8983/solr/
```

### RabbitMQ (`mq` Service)

#### Access RabbitMQ Management Interface

RabbitMQ management runs on port `15672`. Access it via:

```
http://localhost:15672/
```

- **Username:** `guest`
- **Password:** `guest`

### Celery Worker (`worker` Service)

Logs for the Celery worker can be viewed with:

```bash
docker compose logs -f worker
```

### Celery Beat (`beat` Service)

Logs for Celery Beat can be viewed with:

```bash
docker compose logs -f beat
```

### Flower Monitoring Tool (`flower` Service)

Access Flower for task monitoring on port `5555`:

```
http://localhost:5555/
```

---

## Backup and Restore Operations

### Backup Service (`backup`)


#### Manual Backup

Create a manual backup:



```bash
chmod +x ./backup_script.sh && ./backup_script.sh
```
or

```bash
docker compose stop nginx flower worker beat web mq solr
docker compose exec backup sh /code/scripts/db.sh backup
docker compose up -d solr mq web worker beat flower nginx
```

Backup files are stored in the `BACKUP_DIR` (default is `../backups`).

### Restore from Backup

Restore from a specific backup file:

```bash
docker compose stop nginx flower worker beat web mq solr
docker compose exec backup sh /code/scripts/db.sh restore ../backups/backup_<timestamp>.tar.gz
docker compose up -d solr mq web worker beat flower nginx
```

Replace `<timestamp>` with the actual timestamp in the backup filename.

Rebuild the Solr index after restoration:

```bash
docker compose exec web python manage.py rebuild_index --noinput
```

#### Scheduled Backup with Cron

To schedule the backup script to run automatically at a specific time using cron, add the following line to your crontab:

1. Open the crontab editor:

    ```bash
    crontab -e
    ```

2. Add the cron job entry (for example, to run the backup at 1 AM daily):

    ```bash
    0 1 * * * /path/to/backup_script.sh
    ```

3. Check if the cron job is added:

    ```bash
    docker compose exec backup crontab -l
    ```

Replace `/path/to/backup_script.sh` with the actual path to backup_script.


### Restore Legacy Backup

To restore from a legacy backup file (e.g., `daisy_prod.tar.gz`):

```bash
docker compose stop nginx flower worker beat web mq solr

# Copy the legacy backup file into the backup container
docker cp ../daisy_prod.tar.gz $(docker compose ps -q backup):/code/daisy_prod.tar.gz

# Execute the legacy restore script inside the backup container
docker compose exec backup sh /code/scripts/legacy_restore.sh /code/daisy_prod.tar.gz

# Remove the backup file from the container
docker compose exec backup rm /code/daisy_prod.tar.gz

docker compose up -d solr mq web worker beat flower nginx

# Rebuild the Solr index
docker compose exec web python manage.py rebuild_index --noinput
```

---

## Importing and Exporting Data

### Import Data

You can import data from JSON files using Django management commands.

#### Import Projects

```bash
docker compose exec web python manage.py import_projects -f /path/to/projects.json
```

#### Import Datasets

```bash
docker compose exec web python manage.py import_datasets -f /path/to/datasets.json
```

#### Import Partners

```bash
docker compose exec web python manage.py import_partners -f /path/to/partners.json
```

To import multiple JSON files from a directory:

```bash
docker compose exec web python manage.py import_projects -d /path/to/directory/
```

### Export Data

Export data to JSON files.

#### Export Projects

```bash
docker compose exec web python manage.py export_projects -f /path/to/output/projects.json
```

#### Export Datasets

```bash
docker compose exec web python manage.py export_datasets -f /path/to/output/datasets.json
```

#### Export Partners

```bash
docker compose exec web python manage.py export_partners -f /path/to/output/partners.json
```

---

## Updating the Project

### Pull Latest Changes

```bash
git pull origin main
```

### Rebuild Services After Code Changes

If you make changes to the code or dependencies, rebuild the affected services:

```bash
docker compose build web worker beat
docker compose up -d
```

### Database Backup Before Upgrade

Create a database backup before upgrading:

```bash
docker compose exec backup sh /code/scripts/db.sh backup
```

### Upgrade Steps

1. **Pull Latest Changes:**

    ```bash
    git pull origin main
    ```

2. **Rebuild Docker Images:**

    ```bash
    docker compose build
    ```

3. **Apply Database Migrations:**

    ```bash
    docker compose exec web python manage.py migrate
    ```

4. **Update Solr Schema:**

    ```bash
    docker compose exec web python manage.py build_solr_schema -c /solr/daisy/conf -r daisy -u default
    ```

5. **Collect Static Files:**

    ```bash
    docker compose exec web python manage.py collectstatic --noinput
    ```

6. **Rebuild Search Index:**

    ```bash
    docker compose exec web python manage.py rebuild_index --noinput
    ```

7. **Optional - Import Users:**

    If you use LDAP or Active Directory:

    ```bash
    docker compose exec web python manage.py import_users
    ```

---

## Administration

To access the admin interface:

1. **Create a Superuser Account:**

    ```bash
    docker compose exec web python manage.py createsuperuser
    ```

2. **Access the Admin Site:**

    ```
    http://localhost/admin/
    ```

    Log in with your superuser credentials.

---

## Settings Reference

Adjust the `elixir_daisy/settings_compose.py` file to configure the application.

### Display Settings

- **`COMPANY`**: Name used in model verbose names.
- **`DEMO_MODE`**: Set to `True` to display a demo banner.
- **`INSTANCE_LABEL`**: Label displayed in the navbar to differentiate deployments.
- **`INSTANCE_PRIMARY_COLOR`**: Primary color for the navbar.
- **`LOGIN_USERNAME_PLACEHOLDER`**: Placeholder text for the login form username.
- **`LOGIN_PASSWORD_PLACEHOLDER`**: Placeholder text for the login form password.

### Integration with Other Tools

#### ID Service

- **`IDSERVICE_FUNCTION`**: Path to the function generating IDs.
- **`IDSERVICE_ENDPOINT`**: Endpoint for the ID service.

#### REMS Integration

- **`REMS_INTEGRATION_ENABLED`**: Enable REMS integration.
- **`REMS_SKIP_IP_CHECK`**: Skip IP address checks.
- **`REMS_ALLOWED_IP_ADDRESSES`**: List of allowed IP addresses.

#### Keycloak Integration

- **`KEYCLOAK_INTEGRATION`**: Enable Keycloak integration.
- **`KEYCLOAK_URL`**: URL of the Keycloak instance.
- **`KEYCLOAK_REALM_LOGIN`**: Realm login name.
- **`KEYCLOAK_REALM_ADMIN`**: Realm admin name.
- **`KEYCLOAK_USER`**: Username for Keycloak access.
- **`KEYCLOAK_PASS`**: Password for Keycloak access.

### Other Settings

- **`SERVER_SCHEME`**: Scheme (`http` or `https`) for accessing Daisy.
- **`SERVER_URL`**: URL for accessing Daisy (without scheme).
- **`GLOBAL_API_KEY`**: Global API key (disabled if `None`).

---

## Additional Tips

- **Running Custom Commands:** Use `docker compose run` for one-off commands without starting the entire service.

  Example:

  ```bash
  docker compose run --rm web python manage.py shell
  ```

- **Accessing Other Services:** You can shell into other services similarly:

  ```bash
  docker compose exec db /bin/bash
  docker compose exec solr /bin/bash
  ```

- **Environment Variables:** Override environment variables when running commands:

  ```bash
  DB_NAME=custom_db docker compose up -d
  ```

---

## Docker Compose Services Overview

- **web:** Django application server using Gunicorn.
- **db:** PostgreSQL database.
- **nginx:** Reverse proxy and static file server.
- **solr:** Apache Solr for full-text search.
- **mq:** RabbitMQ message broker.
- **flower:** Monitoring tool for Celery tasks.
- **worker:** Celery worker for asynchronous tasks.
- **beat:** Celery Beat scheduler.
- **backup:** Manages database backups and restoration.

---

## Logs and Monitoring

### View Service Logs

View logs for a specific service:

```bash
docker compose logs -f <service_name>
```

Replace `<service_name>` with `web`, `db`, `worker`, etc.

### Check Container Status

```bash
docker compose ps
```

---

## Clean Up

### Remove All Containers and Volumes

Stop containers and remove containers, networks, volumes, and images:

```bash
docker system prune -a
docker compose down -v --rmi all
```



