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

To get access to the admin page, you must log in with a superuser account.  
On the `Users` section, you can give any user a `staff` status and he will be able to access any project/datasets.

### `local_settings.py` reference

#### Display

| Key                          | Description                                                                      | Expected values | Example value                  |
| ---------------------------- | -------------------------------------------------------------------------------- | --------------- | ------------------------------ |
| `COMPANY`                    | A name that is used to generate verbose names of some models                     | str             | `'LCSB'`                       |
| `DEMO_MODE`                  | A flag which makes a simple banneer about demo mode appear in About page         | bool            | `False`                        |
| `INSTANCE_LABEL`             | A name that is used in navbar header to help differentiate different deployments | str             | `'Staging test VM'`            |
| `INSTANCE_PRIMARY_COLOR`     | A color that will be navbar header's background                                  | str of a color  | `'#076505'`                    |
| `LOGIN_USERNAME_PLACEHOLDER` | A helpful placeholder in login form for logins                                   | str             | `'@uni.lu'`                    |
| `LOGIN_PASSWORD_PLACEHOLDER` | A helpful placeholder in login form for passwords                                | str             | `'Hint: use your AD password'` |

#### Integration with other tools

##### ID Service

| Key                  | Description                                                                               | Expected values | Example value                              |
| -------------------- | ----------------------------------------------------------------------------------------- | --------------- | ------------------------------------------ |
| `IDSERVICE_FUNCTION` | Path to a function (`lambda: str`) that generates IDs for entities which are published    | str             | `'web.views.utils.generate_elu_accession'` |
| `IDSERVICE_ENDPOINT` | In case LCSB's idservice function is being used, the setting contains the IDservice's URI | str             | `'https://192.168.1.101/v1/api/`           |

##### REMS

| Key                         | Description                                                                                                                                                                                  | Expected values | Example value                    |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | -------------------------------- |
| `REMS_INTEGRATION_ENABLED`  | A feature flag for REMS integration. In practice, there's a dedicated endpoint which processes the information from REMS about dataset entitlements                                          | str             | `True`                           |
| `REMS_SKIP_IP_CHECK`        | If set to `True`, there will be no IP checking if the request comes from trusted REMS instance.                                                                                              | bool            | `False`                          |
| `REMS_ALLOWED_IP_ADDRESSES` | A list of IP addresses that should be considered trusted REMS instances. Beware of configuration difficulties when using reverse proxies. The check can be skipped with `REMS_SKIP_IP_CHECK` | dict[str]       | `['127.0.0.1', '192.168.1.101']` |

##### Keycloak

| Key                    | Description                                                            | Expected values | Example value                          |
| ---------------------- | ---------------------------------------------------------------------- | --------------- | -------------------------------------- |
| `KEYCLOAK_INTEGRATION` | A feature flag for importing user information from Keycloak (OIDC IDs) | bool            | `True`                                 |
| `KEYCLOAK_URL`         | URL to the Keycloak instance                                           | str             | `'https://keycloak.lcsb.uni.lu/auth/'` |
| `KEYCLOAK_REALM_LOGIN` | Realm's login name in your Keycloak instance                           | str             | `'master'`                             |
| `KEYCLOAK_REALM_ADMIN` | Realm's admin name in your Keycloak instance                           | str             | `'master'`                             |
| `KEYCLOAK_USER`        | Username to access Keycloak                                            | str             | `'username'`                           |
| `KEYCLOAK_PASS`        | Password to access Keycloak                                            | str             | `'secure123'`                          |

#### Others

| Key              | Description                                                               | Expected values | Example value                                            |
| ---------------- | ------------------------------------------------------------------------- | --------------- | -------------------------------------------------------- |
| `SERVER_SCHEME`  | A URL's scheme to access your DAISY instance (http or https)              | str             | `'https'`                                                |
| `SERVER_URL`     | A URL to access your DAISY instance (without the scheme)                  | str             | `'example.com'`                                          |
| `GLOBAL_API_KEY` | An API key that is not connected with any user. Disabled if set to `None` | optional[str]   | `'in-practice-you-dont-want-to-use-it-unless-debugging'` |

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
