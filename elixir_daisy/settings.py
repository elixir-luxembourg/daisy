import os
import pytz
from pathlib import Path

import environ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(
    ENVIRONMENT=(str, "local"),
    DEBUG=(bool, None),
    SECRET_KEY=(str, None),
    GLOBAL_API_KEY=(str, None),
)

DOTENV_BASE = Path(BASE_DIR)
env_name = os.environ.get("ENVIRONMENT", "local")
if env_name:
    candidate = DOTENV_BASE / f".env.{env_name}"
    if candidate.exists():
        environ.Env.read_env(str(candidate))

DOTENV_PATH = DOTENV_BASE / ".env"
if os.environ.get("DJANGO_READ_DOTENV", str(DOTENV_PATH.exists())).lower() in (
    "1",
    "true",
    "yes",
):
    environ.Env.read_env(str(DOTENV_PATH))

ENVIRONMENT = env("ENVIRONMENT")

DEBUG = env.bool("DEBUG", default=(ENVIRONMENT == "local"))

# Secret key
SECRET_KEY = env("SECRET_KEY", default=None)
if ENVIRONMENT == "production" and not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set in production via environment variable")

# Basic metadata
COMPANY = env("COMPANY", default="LCSB")
DEMO_MODE = env.bool("DEMO_MODE", default=False)
INSTANCE_LABEL = env("INSTANCE_LABEL", default=None)
INSTANCE_PRIMARY_COLOR = env("INSTANCE_PRIMARY_COLOR", default=None)
AUTH_USER_MODEL = env("AUTH_USER_MODEL", default="core.User")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
SESSION_COOKIE_SECURE = env.bool(
    "SESSION_COOKIE_SECURE", default=(ENVIRONMENT != "local")
)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=(ENVIRONMENT != "local"))
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Login URLs
LOGIN_REDIRECT_URL = env("LOGIN_REDIRECT_URL", default="dashboard")
LOGIN_URL = env("LOGIN_URL", default="login")

# REMS integration
REMS_INTEGRATION_ENABLED = env.bool("REMS_INTEGRATION_ENABLED", default=False)
REMS_URL = env("REMS_URL", default=env("REMS_URL", default=""))
REMS_API_USER = env("REMS_API_USER", default="")
REMS_API_KEY = env("REMS_API_KEY", default="")
REMS_VERIFY_SSL = env.bool("REMS_VERIFY_SSL", default=True)
REMS_RETRIES = env.int("REMS_RETRIES", default=3)
REMS_SKIP_IP_CHECK = env.bool("REMS_SKIP_IP_CHECK", default=False)
REMS_ALLOWED_IP_ADDRESSES = env.list("REMS_ALLOWED_IP_ADDRESSES", default=[])

# Haystack connections
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.solr_backend.SolrEngine",
        "URL": env("SOLR_URL", default="http://localhost:8983/solr/daisy"),
        "ADMIN_URL": env(
            "SOLR_ADMIN_URL", default="http://localhost:8983/solr/admin/cores"
        ),
    },
    "test": {
        "ENGINE": "haystack.backends.solr_backend.SolrEngine",
        "URL": env("SOLR_URL_TEST", default="http://solr:8983/solr/daisy_test"),
        "ADMIN_URL": env("SOLR_ADMIN_URL", default="http://solr:8983/solr/admin/cores"),
    },
}

# http://celery-haystack.readthedocs.io/en/latest/#usage
HAYSTACK_SIGNAL_PROCESSOR = env(
    "HAYSTACK_SIGNAL_PROCESSOR",
    default="celery_haystack.signals.CelerySignalProcessor",
)

# Application definition
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "haystack",
    "guardian",
    "formtools",
    "widget_tweaks",
    "core.apps.CoreConfig",
    "web.apps.WebConfig",
    "notification.apps.NotificationConfig",
    "django.contrib.admin",
    "debug_toolbar",
    "django_celery_results",
    "django_celery_beat",
    "celery_haystack",
    "sequences.apps.SequencesConfig",
    "auditlog",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
]

ROOT_URLCONF = "elixir_daisy.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "web.views.context_processors.daisy_version",
                "web.views.context_processors.instance_branding",
                "notification.views.context_processors.daisy_notifications_enabled",
            ],
        },
    },
]

WSGI_APPLICATION = "elixir_daisy.wsgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://daisy:daisy@localhost:5432/daisy",
    )
}

# For test/ci environments, use template0 to avoid PostgreSQL collation version issues
if ENVIRONMENT in ("test", "ci"):
    DATABASES["default"]["TEST"] = {
        "TEMPLATE": "template0",
    }

# Authentication backend
# https://django-guardian.readthedocs.io/en/stable/configuration.html
AUTHENTICATION_BACKENDS = env.list(
    "AUTHENTICATION_BACKENDS",
    default=[
        "django.contrib.auth.backends.ModelBackend",
        "guardian.backends.ObjectPermissionBackend",
    ],
)

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Luxembourg"
TZINFO = pytz.timezone(TIME_ZONE)
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Celery configs
CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL", default="amqp://guest:guest@localhost:5672//"
)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="django-db")
CELERY_TIMEZONE = env("CELERY_TIMEZONE", default=TIME_ZONE)

# Static files (CSS, JavaScript, Images)
STATIC_URL = env("STATIC_URL", default="/static/")
STATIC_ROOT = env("STATIC_ROOT", default=os.path.join(BASE_DIR, "staticfiles"))
MEDIA_ROOT = env("MEDIA_ROOT", default="/code/medias/")
SASS_PROCESSOR_ROOT = env("SASS_PROCESSOR_ROOT", default=STATIC_ROOT)

INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"])

EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default=(
        "django.core.mail.backends.console.EmailBackend"
        if DEBUG
        else "django.core.mail.backends.smtp.EmailBackend"
    ),
)
EMAIL_DONOTREPLY = env("EMAIL_DONOTREPLY", default="do-not-reply@daisy.lcsb.uni.lu")

# server settings
SERVER_SCHEME = "https"
SERVER_URL = "example.com"

HELPDESK_EMAIL = env("HELPDESK_EMAIL", default="support@example.com")

LOGFILE_MAX_BYTES = env.int("LOGFILE_MAX_BYTES", default=16777216)  # 16MB
LOG_DIR = env("LOG_DIR", default=os.path.join(BASE_DIR, "log"))
LOG_LEVEL = env("LOG_LEVEL", default=("DEBUG" if DEBUG else "ERROR"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "sql": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": LOGFILE_MAX_BYTES,
            "backupCount": 10,
            "filters": ["require_debug_true"],
            "filename": os.path.join(LOG_DIR, "daisy.sql.log"),
            "formatter": "verbose",
        },
        "logfile": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": LOGFILE_MAX_BYTES,
            "backupCount": 10,
            "filename": os.path.join(LOG_DIR, "daisy.log"),
            "formatter": "verbose",
        },
        "templates": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": LOGFILE_MAX_BYTES,
            "backupCount": 1,
            "filters": ["require_debug_true"],
            "filename": os.path.join(LOG_DIR, "daisy.template_errors.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["mail_admins", "console", "logfile"],
            "propagate": True,
            "level": LOG_LEVEL,
        },
        "django.request": {
            "handlers": ["mail_admins", "console", "logfile"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
        "django.template": {
            "handlers": ["templates"],
            "propagate": False,
            "level": LOG_LEVEL,
        },
        "django.db.backends": {
            "handlers": ["mail_admins", "sql"],
            "propagate": False,
            "level": LOG_LEVEL,
        },
        "django.utils.autoreload": {
            "level": "INFO",
        },
        "daisy": {
            "handlers": ["mail_admins", "console", "logfile"],
            "level": LOG_LEVEL,
            "propagate": True,
        },
    },
}

# search settings
FACET_FIELDS = {
    "dataset": (
        "local_custodians",
        "consent_status",
        "data_types",
        "deidentification_method",
        "is_published",
    ),
    "contract": (
        "name",
        "contacts",
        "partners",
        "project",
        "has_legal_documents",
    ),
    "project": (
        "local_custodians",
        "start_year",
        "end_year",
        "disease_terms",
        "study_terms",
        "phenotype_terms",
        "gene_terms",
        "has_cner",
        "has_erp",
        "has_legal_documents",
        "funding_sources",
        "company_personnel",
        "contacts",
    ),
    "cohort": ("owners", "institutes"),
    "partner": ("geo_category", "sector_category", "is_clinical"),
    "contact": ("type", "partners"),
    "dac": ("local_custodians", "project"),
}

# by default, notifications by email are disabled
NOTIFICATIONS_DISABLED = False
ADMIN_NOTIFICATIONS_EMAIL = env("ADMIN_NOTIFICATIONS_EMAIL", default="")

# Placeholders on login page
LOGIN_USERNAME_PLACEHOLDER = env("LOGIN_USERNAME_PLACEHOLDER", default="")
LOGIN_PASSWORD_PLACEHOLDER = env("LOGIN_PASSWORD_PLACEHOLDER", default="")

# Custom error view, see e.g.
CSRF_FAILURE_VIEW = "web.views.error_views.custom_csrf"

# JSON schemas used for validation on import
IMPORT_JSON_SCHEMAS_URI = (
    "https://raw.githubusercontent.com/elixir-luxembourg/json-schemas/v0.0.6/schemas/"
)
IMPORT_JSON_SCHEMAS_DIR = os.path.join(BASE_DIR, "core", "fixtures", "json_schemas")

ACCESS_DEFAULT_EXPIRATION_DAYS = env.int("ACCESS_DEFAULT_EXPIRATION_DAYS", default=90)
IDSERVICE_FUNCTION = env(
    "IDSERVICE_FUNCTION", default="web.views.utils.generate_elu_accession"
)

# Data Stewardship Wizard - pop up integration
DSW_ORIGIN = env("DSW_ORIGIN", default="localhost")

# Should the superuser be able to change the passwords in django-admin
ENABLE_PASSWORD_CHANGE_IN_ADMIN = env.bool(
    "ENABLE_PASSWORD_CHANGE_IN_ADMIN", default=False
)

# Keycloak integration, uncomment and fill the values below
KEYCLOAK_URL = env("KEYCLOAK_URL", default="https://sso.lcsb.uni.lu/")
KEYCLOAK_REALM_LOGIN = env("KEYCLOAK_REALM_LOGIN", default="End-2-End-Testing")
KEYCLOAK_REALM_ADMIN = env("KEYCLOAK_REALM_ADMIN", default="End-2-End-Testing")
KEYCLOAK_USER = env("KEYCLOAK_USER", default="")
KEYCLOAK_PASS = env("KEYCLOAK_PASS", default="")
KEYCLOAK_INTEGRATION = env("KEYCLOAK_INTEGRATION", default=False)

if OIDC_METADATA_URL := env("OIDC_METADATA_URL", default=""):
    AUTHLIB_OAUTH_CLIENTS = {
        "keycloak": {
            "client_id": env("OIDC_CLIENT_ID", default=""),
            "client_secret": env("OIDC_CLIENT_SECRET", default=""),
            "server_metadata_url": OIDC_METADATA_URL,
            "client_kwargs": {"scope": "openid email profile"},
        }
    }

if DEBUG:
    # Removing staticfiles panel from Django Debug Toolbar
    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ]

# Local/global API key
GLOBAL_API_KEY = env("GLOBAL_API_KEY", default=None)
if ENVIRONMENT not in ("local", "development") and not GLOBAL_API_KEY:
    raise RuntimeError("GLOBAL_API_KEY must be set in non-local environments")

# if LDAP authentication will be used and user definitions will be bulk imported from LDAP
if env.bool("LDAP_ENABLED", default=False):
    import ldap
    from django_auth_ldap.config import LDAPSearch

    # Prepend the LDAP backend to the auth backends when enabled
    AUTHENTICATION_BACKENDS = [
        "django_auth_ldap.backend.LDAPBackend",
    ] + AUTHENTICATION_BACKENDS

    # LDAP connection and search settings (can be overridden via env)
    AUTH_LDAP_SERVER_URI = env("AUTH_LDAP_SERVER_URI", default="ldap://localhost/")
    AUTH_LDAP_BIND_DN = env(
        "AUTH_LDAP_BIND_DN",
        default="CN=Normal.User,OU=LCSB,OU=Faculties,OU=UNI-Users,DC=uni,DC=lux",
    )
    AUTH_LDAP_BIND_PASSWORD = env("AUTH_LDAP_BIND_PASSWORD", default="")

    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        env(
            "AUTH_LDAP_USER_SEARCH_BASE",
            default="OU=Faculties,OU=UNI-Users,DC=uni,DC=lux",
        ),
        ldap.SCOPE_SUBTREE,
        env("AUTH_LDAP_USER_SEARCH_FILTER", default="(userPrincipalName=%(user)s)"),
    )

    AUTH_LDAP_USER_ATTR_MAP = {
        "first_name": env("AUTH_LDAP_USER_ATTR_MAP_FIRST_NAME", default="givenName"),
        "last_name": env("AUTH_LDAP_USER_ATTR_MAP_LAST_NAME", default="sn"),
        "email": env("AUTH_LDAP_USER_ATTR_MAP_EMAIL", default="mail"),
    }

    LDAP_USERS_IMPORT_CLASS = env(
        "LDAP_USERS_IMPORT_CLASS", default="(objectClass=person)"
    )
    LDAP_USERS_IMPORT_USERNAME_ATTR = env(
        "LDAP_USERS_IMPORT_USERNAME_ATTR", default="userprincipalname"
    )
    AUTH_LDAP_USER_DN_TEMPLATE = env(
        "AUTH_LDAP_USER_DN_TEMPLATE",
        default="CN=%(user)s,OU=LCSB,OU=Faculties,OU=UNI-Users,DC=uni,DC=lux",
    )
    LDAP_USERS_IMPORT_SEARCH_DN = env(
        "LDAP_USERS_IMPORT_SEARCH_DN",
        default="OU=LCSB,OU=Faculties,OU=UNI-Users,DC=uni,DC=lux",
    )

# list of usernames of users that will imported and set as pi when
# import_users is used to bulk create users from an LDAP server
PREDEFINED_PIS_LIST = [
    # "name.surname@uni.lu", "othername.othersurname@uni.lu",
]


# IDSERVICE_FUNCTION = 'core.lcsb.idservice.generate_identifier'
IDSERVICE_ENDPOINT = env(
    "IDSERVICE_ENDPOINT", default="https://10.240.16.199:8080/v1/api/id"
)

# Celery beat setting to schedule tasks on docker creation
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "clean-accesses-every-day": {
        "task": "core.tasks.check_accesses_expiration",
        "schedule": crontab(minute=0, hour=0),  # Execute task at midnight
    },
    "create-notifications-every-day": {
        "task": "notification.tasks.create_notifications_for_entities",
        "schedule": crontab(minute=15, hour=0),
    },
    "notifications-email-every-day": {
        "task": "notification.tasks.send_notifications_for_user_upcoming_events",
        "schedule": crontab(minute=0, hour=7),  # Execute task in the morning
    },
    "synchronizer-every-day": {
        "task": "core.tasks.run_synchronizer",
        "schedule": crontab(minute=0, hour=2),  # Execute task at 2am
    },
    "update-rems-application-external-id": {
        "task": "core.tasks.update_rems_access_external_id",
        "schedule": crontab(minute=0, hour=3),  # Execute task at 3am
    },
}

# Test environment detection
TESTING = os.environ.get("TEST", False)

# Password hashers (can be overridden for faster tests in CI)
if password_hashers := env.list("PASSWORD_HASHERS", default=None):
    PASSWORD_HASHERS = password_hashers
