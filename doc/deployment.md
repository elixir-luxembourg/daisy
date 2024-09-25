# Daisy Project Setup Guide

This guide provides concise instructions for setting up and running the Daisy project using Docker Compose. It includes commands for managing the Django application and other services within the project.

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

Create a `.env` file in the project root to override default environment variables if necessary. See [.env.template](env.template) file for more detail.

## Installation

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

In case you are provisioning a demo instance, following command loads demo data, including mock datasets, projects, and a demo admin account:

```bash
docker compose exec web python manage.py load_demo_data
```

You can log in with the demo admin credentials provided during the demo data setup (username: `admin`, password:`admin` by default) or as one of the regular users (see the `About` page for more detail).

### Build the Search Index

After loading data, build the search index for Solr:

```bash
docker compose exec web python manage.py rebuild_index --noinput
```

### Access the Application

The application should now be accessible at:

- **HTTP:** `http://localhost/`
- **HTTPS:** `https://localhost/`

## Scheduled Backup with Cron

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
