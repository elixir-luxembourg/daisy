# These settings are used in local Docker environment (see docker-compose.yaml)
from django_auth_ldap.config import LDAPSearch
from .settings import *  # noqa: F401,F403

import ldap
import os

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "daisy",
        "USER": "daisy",
        "PASSWORD": "daisy",
        "HOST": "db",
        "PORT": 5432,
    }
}

AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend",
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

AUTH_LDAP_SERVER_URI = "ldap://localhost/"
AUTH_LDAP_BIND_DN = "CN=Normal.User,OU=LCSB,OU=Faculties,OU=UNI-Users,DC=uni,DC=lux"
AUTH_LDAP_BIND_PASSWORD = "password"
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "OU=Faculties,OU=UNI-Users,DC=uni,DC=lux",
    ldap.SCOPE_SUBTREE,
    "(userPrincipalName=%(user)s)",
)
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}
LDAP_USERS_IMPORT_CLASS = "(objectClass=person)"
LDAP_USERS_IMPORT_USERNAME_ATTR = "userprincipalname"
AUTH_LDAP_USER_DN_TEMPLATE = (
    "CN=%(user)s,OU=LCSB,OU=Faculties,OU=UNI-Users,DC=uni,DC=lux"
)
LDAP_USERS_IMPORT_SEARCH_DN = "OU=LCSB,OU=Faculties,OU=UNI-Users,DC=uni,DC=lux"

# Haystack connections
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.solr_backend.SolrEngine",
        "URL": "http://solr:8983/solr/daisy",
        "ADMIN_URL": "http://solr:8983/solr/admin/cores",
    },
    "test": {
        "ENGINE": "haystack.backends.solr_backend.SolrEngine",
        "URL": "http://solr:8983/solr/daisy_test",
        "ADMIN_URL": "http://solr:8983/solr/admin/cores",
    },
}

# http://celery-haystack.readthedocs.io/en/latest/#usage
HAYSTACK_SIGNAL_PROCESSOR = "celery_haystack.signals.CelerySignalProcessor"

STATIC_ROOT = "/static"
SASS_PROCESSOR_ROOT = "/static"

# Celery config
# http://docs.celeryproject.org/en/latest/userguide/configuration.html

# Broker settings.
CELERY_BROKER_URL = "amqp://guest:guest@mq:5672//"

# Result backend
CELERY_RESULT_BACKEND = "django-db"

TESTING = os.environ.get("TEST", False)

# import also local settings
try:
    from .settings_local import *  # noqa: F401,F403

    if TESTING:
        from .settings_ci import *  # noqa: F401,F403
except ImportError:
    pass
