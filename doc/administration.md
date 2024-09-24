# Managing

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
