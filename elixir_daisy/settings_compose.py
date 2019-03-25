from .settings import *


# Haystack connections
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://solr:8983/solr/daisy',
        'ADMIN_URL': 'http://solr:8983/solr/admin/cores',
    },
    'test': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://solr:8983/solr/daisy_test',
        'ADMIN_URL': 'http://solr:8983/solr/admin/cores',
    },
}

# http://celery-haystack.readthedocs.io/en/latest/#usage
HAYSTACK_SIGNAL_PROCESSOR = 'celery_haystack.signals.CelerySignalProcessor'

STATIC_ROOT = '/static'
SASS_PROCESSOR_ROOT = '/static'

# Celery config
# http://docs.celeryproject.org/en/latest/userguide/configuration.html

## Broker settings.
CELERY_BROKER_URL = 'amqp://guest:guest@mq:5672//'

## Result backend
CELERY_RESULT_BACKEND = 'django-db'

TESTING = os.environ.get('TEST', False)

# import also local settings
try:
    if TESTING:
        from .settings_ci import *
except ImportError as e:
    pass

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'daisy',
        'USER': 'daisy',
        'PASSWORD': 'daisy',
        'HOST': 'db',
        'PORT': 5432,
    }
}
