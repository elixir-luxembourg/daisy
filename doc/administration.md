# Management and administration

## Access the Web Service

Shell into the `web` container:

```bash
docker compose exec web /bin/bash
```

### Run Django Commands

Run Django management commands, e.g. `makemigrations`, `migrate`, `createsuperuser`, etc., using the `web` service:


```bash
docker compose exec web python manage.py <django-command>
```

See `docker compose exec web python manage.py --help` for all available commands.

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

DAISY loads configuration from `.env.{ENVIRONMENT}` files. Use the interactive script to generate a production or staging config:

```bash
./scripts/create_env.sh
```

### Environment Variables Reference

#### Core Settings

Defaults work for development; **production requires explicit configuration**.

| Key                   | Description                                                            | Required for Production | Default value                                  |
| --------------------- | ---------------------------------------------------------------------- | ----------------------- | ---------------------------------------------- |
| `ENVIRONMENT`         | Environment name (development, production, test)                       | No                      | `'development'`                                |
| `SECRET_KEY`          | Django secret key for cryptographic signing                            | **Yes**                 | None                                           |
| `GLOBAL_API_KEY`      | API authentication key                                                 | **Yes**                 | None                                           |
| `DATABASE_URL`        | PostgreSQL connection string                                           | **Yes**                 | `'postgresql://daisy:daisy@db:5432/daisy'`    |
| `CELERY_BROKER_URL`   | RabbitMQ message broker URL                                            | **Yes**                 | `'amqp://guest:guest@mq:5672//'`              |
| `SOLR_URL`            | Solr search engine URL                                                 | **Yes**                 | `'http://solr:8983/solr/daisy'`               |
| `SOLR_URL_TEST`       | Solr test core URL                                                     | No                      | `'http://solr:8983/solr/daisy_test'`          |
| `SOLR_ADMIN_URL`      | Solr admin interface URL                                               | **Yes**                 | `'http://solr:8983/solr/admin/cores'`         |
| `ALLOWED_HOSTS`       | Comma-separated list of allowed hostnames                              | **Yes**                 | `'*'`                                          |
| `CSRF_TRUSTED_ORIGINS`| Comma-separated list of trusted origins (with scheme)                  | **Yes**                 | `[]`                                           |

#### Display Settings

| Key                          | Description                                                                      | Expected values | Default value                  |
| ---------------------------- | -------------------------------------------------------------------------------- | --------------- | ------------------------------ |
| `COMPANY`                    | Company/organization name used in verbose model names                            | str             | `'LCSB'`                       |
| `DEMO_MODE`                  | Show demo mode banner on About page                                              | bool            | `False`                        |
| `INSTANCE_LABEL`             | Label shown in navbar to differentiate deployments                               | str             | `None`                         |
| `INSTANCE_PRIMARY_COLOR`     | Navbar background color                                                          | str (color)     | `None`                         |
| `LOGIN_USERNAME_PLACEHOLDER` | Placeholder text in login form username field                                    | str             | `''`                           |
| `LOGIN_PASSWORD_PLACEHOLDER` | Placeholder text in login form password field                                    | str             | `''`                           |

#### Integration with other tools

##### ID Service

| Key                  | Description                                                                               | Expected values | Default value                              |
| -------------------- | ----------------------------------------------------------------------------------------- | --------------- | ------------------------------------------ |
| `IDSERVICE_FUNCTION` | Path to function that generates IDs for published entities                                | str             | `'web.views.utils.generate_elu_accession'` |
| `IDSERVICE_ENDPOINT` | ID service endpoint URL (if using LCSB's idservice)                                       | str             | `None`                                     |

##### REMS (Resource Entitlement Management System)

| Key                         | Description                                                                                                                                                                                  | Expected values | Default value                    |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | -------------------------------- |
| `REMS_INTEGRATION_ENABLED`  | Enable REMS integration for dataset entitlements                                                                                                                                             | bool            | `False`                          |
| `REMS_URL`                  | REMS instance URL (required if enabled)                                                                                                                                                      | str             | Required when enabled            |
| `REMS_API_USER`             | REMS API username (required if enabled)                                                                                                                                                      | str             | Required when enabled            |
| `REMS_API_KEY`              | REMS API key (required if enabled)                                                                                                                                                           | str             | Required when enabled            |
| `REMS_VERIFY_SSL`           | Verify SSL certificates for REMS connections                                                                                                                                                 | bool            | `True`                           |
| `REMS_SKIP_IP_CHECK`        | Skip IP address validation for REMS requests                                                                                                                                                 | bool            | `False`                          |
| `REMS_ALLOWED_IP_ADDRESSES` | Comma-separated list of trusted REMS IP addresses                                                                                                                                            | str             | `''`                             |

##### Keycloak

| Key                    | Description                                                            | Expected values | Default value                          |
| ---------------------- | ---------------------------------------------------------------------- | --------------- | -------------------------------------- |
| `KEYCLOAK_INTEGRATION` | Enable Keycloak user synchronization                                   | bool            | `False`                                |
| `KEYCLOAK_URL`         | Keycloak instance URL (required if enabled)                            | str             | Required when enabled                  |
| `KEYCLOAK_REALM_LOGIN` | Keycloak login realm name                                              | str             | `'testing'`                  |
| `KEYCLOAK_REALM_ADMIN` | Keycloak admin realm name                                              | str             | `'testing'`                  |
| `KEYCLOAK_USER`        | Keycloak admin username (required if enabled)                          | str             | Required when enabled                  |
| `KEYCLOAK_PASS`        | Keycloak admin password (required if enabled)                          | str             | Required when enabled                  |

##### OIDC (OpenID Connect)

| Key                   | Description                                   | Expected values | Default value           |
| --------------------- | --------------------------------------------- | --------------- | ----------------------- |
| `OIDC_ENABLED`        | Enable OIDC authentication                    | bool            | `False`                 |
| `OIDC_CLIENT_ID`      | OIDC client ID (required if enabled)          | str             | Required when enabled   |
| `OIDC_CLIENT_SECRET`  | OIDC client secret (required if enabled)      | str             | Required when enabled   |
| `OIDC_METADATA_URL`   | OIDC metadata URL (required if enabled)       | str             | Required when enabled   |

##### LDAP

| Key                      | Description                                   | Expected values | Default value           |
| ------------------------ | --------------------------------------------- | --------------- | ----------------------- |
| `LDAP_ENABLED`           | Enable LDAP authentication                    | bool            | `False`                 |
| `AUTH_LDAP_SERVER_URI`   | LDAP server URI (required if enabled)         | str             | Required when enabled   |
| `AUTH_LDAP_BIND_DN`      | LDAP bind DN                                  | str             | `None`                  |
| `AUTH_LDAP_BIND_PASSWORD`| LDAP bind password (required if enabled)      | str             | Required when enabled   |

See `.env.example` for a complete list of all available configuration options.

#### Docker Compose Variables

These variables control infrastructure-level behaviour and must be set in the **root `.env`** file (next to `docker-compose.yaml`). They are **not** read from `.env.development` / `.env.production`.

| Key | Description | Default |
| --- | ----------- | ------- |
| `APP_IMAGE` | Docker image for `web`, `worker`, and `beat` | `daisy:local` |
| `ENV_FILE` | Application env file passed to containers | `.env.development` |
| `LOG_VOLUME` | Named volume or host path mounted at `/code/log`. Use a host path (e.g. `./log`) for direct file access; requires correct ownership. | `logs` (named volume) |
| `BACKUP_VOLUME` | Storage location for backups | `../backups` |

`GUNICORN_LOGLEVEL` and `GUNICORN_ACCESS_LOG` can be set in either the root `.env` or the application env file (e.g. `.env.production`):

| Key | Description | Default |
| --- | ----------- | ------- |
| `GUNICORN_LOGLEVEL` | Gunicorn log verbosity (`debug`, `info`, `warning`, `error`, `critical`) | `info` |
| `GUNICORN_ACCESS_LOG` | Gunicorn access log destination: `/code/log/gunicorn-access.log` (file), `-` (stdout), or unset (disabled) | `/dev/null` |

**Example root `.env` for production:**

```bash
APP_IMAGE=ghcr.io/elixir-luxembourg/daisy:1.x.y
ENV_FILE=.env.production
LOG_VOLUME=./log
```

**Example `.env.production` entries for logging:**

```bash
GUNICORN_LOGLEVEL=warning
GUNICORN_ACCESS_LOG=/code/log/gunicorn-access.log
```

!!! note
    When using a host path for `LOG_VOLUME`, the directory must be writable by the container user (UID 1000 by default):
    ```bash
    sudo chown -R 1000:1000 /opt/daisy/log
    ```

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

View logs streamed to stdout/stderr (gunicorn startup, errors) for a specific service:

```bash
docker compose logs -f <service_name>
```

Replace `<service_name>` with `web`, `db`, `worker`, etc.

### Application Log Files

Django application logs are written to `/code/log/` inside the `web` container, which is backed by the `LOG_VOLUME` (a named Docker volume by default).

**While containers are running:**

```bash
docker compose exec web tail -f /code/log/daisy.log
```

**After `docker compose down`** (named volume persists):

```bash
docker run --rm -v daisy_logs:/code/log alpine cat /code/log/daisy.log
```

To find the exact volume name:

```bash
docker volume ls | grep logs
```

**Using a host bind mount** (set `LOG_VOLUME=./log` in root `.env`):

```bash
cat ./log/daisy.log
```

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

## Importing and Exporting Data

In addition to loading of initial data, DAISY database can be populated by importing Project, Dataset and Partners records from JSON files using commands `import_projects`, `import_datasets` and `import_partners` respectively. JSON files are validated using the [Elixir-LU JSON schemas](https://github.com/elixir-luxembourg/json-schemas).

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

Information in the DAISY database can be exported to JSON files. The command for export are given below:</br>

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
