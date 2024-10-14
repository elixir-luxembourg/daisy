# Updating the Project

## Database Backup Before Upgrade

Create a database backup before upgrading:

```bash
docker compose exec backup sh /code/scripts/db.sh backup
```

## Upgrade Steps

1. **Pull Latest Changes:**

    ```bash
    git pull origin master
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
