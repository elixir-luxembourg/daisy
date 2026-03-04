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


# Breaking migrations

## Daisy 1.10.0 to 1.11.0

The settings is fully moved to environment files. Following steps are necessary to migrate to new version:


0. **Before git pull - back up your existing configuration:**

```bash
cp elixir_daisy/settings.py elixir_daisy/settings.py.backup
cp elixir_daisy/settings_compose.py elixir_daisy/settings_compose.py.backup
cp elixir_daisy/settings_local.py elixir_daisy/settings_local.py.backup
```

   **For legacy setups with settings file inheritance (without django-environ):**

   Extract all current settings from your running Docker container:

```bash
docker compose exec -T web python manage.py shell <<'EOF' > settings_backup_$(date +%Y%m%d_%H%M%S).json
from django.conf import settings
import json
settings_list = ['COMPANY', 'DEMO_MODE', 'INSTANCE_LABEL', 'INSTANCE_PRIMARY_COLOR', 'AUTH_USER_MODEL', 'SECRET_KEY', 'DEBUG', 'LOGIN_REDIRECT_URL', 'LOGIN_URL', 'ALLOWED_HOSTS', 'DATABASES', 'AUTHENTICATION_BACKENDS', 'LANGUAGE_CODE', 'TIME_ZONE', 'USE_I18N', 'USE_L10N', 'USE_TZ', 'CELERY_BROKER_URL', 'CELERY_TIMEZONE', 'CELERY_RESULT_BACKEND', 'STATIC_URL', 'STATIC_ROOT', 'MEDIA_ROOT', 'INTERNAL_IPS', 'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_BACKEND', 'EMAIL_DONOTREPLY', 'SERVER_SCHEME', 'SERVER_URL', 'HELPDESK_EMAIL', 'LOGFILE_MAX_BYTES', 'LOG_DIR', 'LOG_LEVEL', 'HAYSTACK_SIGNAL_PROCESSOR', 'NOTIFICATIONS_DISABLED', 'LOGIN_USERNAME_PLACEHOLDER', 'LOGIN_PASSWORD_PLACEHOLDER', 'IMPORT_JSON_SCHEMAS_URI', 'REMS_INTEGRATION_ENABLED', 'REMS_SKIP_IP_CHECK', 'REMS_ALLOWED_IP_ADDRESSES', 'REMS_URL', 'REMS_API_USER', 'REMS_API_KEY', 'REMS_VERIFY_SSL', 'REMS_RETRIES', 'REMS_MATCH_USERS_BY', 'REMS_FORM_ID', 'ACCESS_DEFAULT_EXPIRATION_DAYS', 'IDSERVICE_FUNCTION', 'IDSERVICE_ENDPOINT', 'DSW_ORIGIN', 'ENABLE_PASSWORD_CHANGE_IN_ADMIN', 'KEYCLOAK_INTEGRATION', 'KEYCLOAK_URL', 'KEYCLOAK_REALM_LOGIN', 'KEYCLOAK_REALM_ADMIN', 'KEYCLOAK_USER', 'KEYCLOAK_PASS', 'LDAP_ENABLED', 'AUTH_LDAP_SERVER_URI', 'AUTH_LDAP_BIND_DN', 'AUTH_LDAP_BIND_PASSWORD', 'LDAP_USERS_IMPORT_CLASS', 'LDAP_USERS_IMPORT_USERNAME_ATTR', 'AUTH_LDAP_USER_DN_TEMPLATE', 'LDAP_USERS_IMPORT_SEARCH_DN', 'PREDEFINED_PIS_LIST', 'SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE', 'CSRF_TRUSTED_ORIGINS', 'GLOBAL_API_KEY', 'ENVIRONMENT', 'ADMIN_NOTIFICATIONS_EMAIL', 'HAYSTACK_CONNECTIONS', 'SASS_PROCESSOR_ROOT', 'OIDC_ENABLED']
result = {s: str(getattr(settings, s)) if hasattr(settings, s) else None for s in settings_list}
print(json.dumps(result, indent=2, default=str))
EOF
```

   This extracts all 90+ Django settings variables including:
   - Core settings (DEBUG, SECRET_KEY, ALLOWED_HOSTS, etc.)
   - Database configuration
   - Email settings
   - Celery configuration
   - REMS integration settings
   - LDAP/Keycloak authentication
   - Instance customization
   - And more...

   The command creates a timestamped JSON file like `settings_backup_20251020_143025.json` that you can use to compare with your new settings after the update.

1. **Pull updates**

2. **Create environment file for your deployment:**

   Use the interactive script to create `production` or `staging` env files:

```bash
./scripts/create_env.sh
```

   It also create a .env file with specific for VM variables:

```bash
ENVIRONMENT=staging
ENV_FILE=.env.staging
```

3. **Verify your settings file**

```bash
cat .env
# prod:
cat .env.production
# stage:
cat .env.staging
```

   See [administration documentation](administration.md#environment-variables-reference) for a complete list.

4. **Set environment for VM:**

```bash
docker compose down
docker compose build web
docker compose up -d
```

   This automatically loads env file. You can override with `ENV_FILE` if needed.

5. **Remove old settings files**
