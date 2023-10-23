import os

from celery import Celery

app = Celery("daisy")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
# The uppercase name-space means that all Celery configuration options must
#  be specified in uppercase instead of lowercase, and start with CELERY_,
#  so for example the task_always_eager setting becomes CELERY_TASK_ALWAYS_EAGER,

app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
