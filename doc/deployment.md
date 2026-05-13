# Daisy Project Setup Guide

This guide provides concise instructions for setting up and running the Daisy project using Docker Compose. It includes commands for managing the Django application and other services within the project.

!!! info
    For legacy deployment (<1.8.1), please refer to the [Legacy deployment and administration manual](legacy-deployment.md).

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

### Environment Configuration

DAISY loads configuration from `.env.{ENVIRONMENT}` files (default: `.env.development`).

**For production or staging**, generate a secure configuration:

```bash
./scripts/create_env.sh
```

Then start services with:

```bash
docker compose up -d
```

See [administration.md](administration.md#environment-variables-reference) for all available settings.

## Installation

### Configure Nginx

Choose one of the supported production topologies:

- Container nginx: keep using the `nginx` Compose service.
- Host nginx + Dockerized app: run nginx on the VM and proxy to the `web` container on `127.0.0.1:5000`.

#### Container nginx

Copy the Nginx configuration template:

```bash
cp ./docker/nginx/nginx.conf.template ./docker/nginx/nginx.conf
```

Customize `nginx.conf` as needed and then start or restart the Nginx service:

```bash
docker compose restart nginx
```

#### Host nginx + Dockerized app

The app is published on loopback only (`127.0.0.1:5000`). Host nginx proxies requests to it and serves static files directly from a bind-mounted host directory (`./staticfiles`). The `web` container populates that directory automatically via `collectstatic` on every startup.

**One-time setup on the VM:**

```bash
# Create staticfiles dir on local filesystem with correct SELinux context.
# Must be done before starting the stack so files written by Docker inherit the context.
sudo mkdir -p /var/www/daisy/staticfiles
sudo chown -R 1000:1000 /var/www/daisy/staticfiles
sudo chcon -Rt httpd_sys_content_t /var/www/daisy/staticfiles
sudo semanage fcontext -a -t httpd_sys_content_t "/var/www/daisy/staticfiles(/.*)?"

# Install and configure nginx
sudo dnf install nginx -y
sudo cp /home/daisy/daisy/docker/nginx/nginx.conf.manual /etc/nginx/nginx.conf
sudo vi /etc/nginx/nginx.conf   # set server_name and ssl_certificate paths
sudo nginx -t && sudo systemctl enable --now nginx
```

Set these in your production env file:

```env
ALLOWED_HOSTS=daisy.example.org
CSRF_TRUSTED_ORIGINS=https://daisy.example.org
```

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

### Initialize Solr Search Index

Solr uses a managed schema (fields are created from the Django search indexes). Ensure Solr is running, then build the index.

```bash
docker compose up -d solr
curl -s "http://localhost:8983/solr/admin/cores?action=STATUS&wt=json" | jq .
curl -s "http://localhost:8983/solr/daisy/schema/fields?wt=json" | jq .
docker compose exec web python manage.py rebuild_index --noinput
```

Replace host/port or drop `| jq .` if `jq` is not available.

### Compile and Deploy Static Files

The project uses frontend assets that need to be compiled (e.g., with npm), you need to build them and collect static files.

#### Install npm Dependencies

```bash
docker compose exec web npm --prefix /static/vendor ci
```

#### Build Frontend Assets

```bash
docker compose exec web npm --prefix /static/vendor run build
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
    wget https://gitlab.lcsb.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/edda.json && \
    wget https://gitlab.lcsb.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hpo.json && \
    wget https://gitlab.lcsb.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hdo.json && \
    wget https://gitlab.lcsb.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hgnc.json
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

The application should now be accessible on `https://localhost/`

## Scheduled Backup with Cron

To ensure the backups are properly set up, please refer to the [Backup manual](backup.md#scheduled-backup-with-cron)

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
