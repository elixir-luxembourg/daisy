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

    Note: Schema auto-generation has issues with Solr 9 ([issue #1986](https://github.com/django-haystack/django-haystack/issues/1986)).

    **Option A - Automated (Recommended):**
    Complete schema update and Solr rebuild:
    # run script to update Solr schema
    ```bash
    docker compose exec web bash -c "cd /code && ./scripts/update_solr_schema.sh"
    ```
    # recreate Solr container
    ```bash
    docker compose down && docker volume rm daisy_solrdata && docker image rm daisy-solr && docker compose up -d
    ```

    **Option B - Manual:**
    Generate schema and manually fix field types:
    ```bash
    docker compose exec web python manage.py build_solr_schema -f docker/solr/schema.xml
    ```
    Then manually update `docker/solr/schema.xml`:
    - Change `LatLonType` to `LatLonPointSpatialField`
    - Remove currency-related fields
    
    

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
