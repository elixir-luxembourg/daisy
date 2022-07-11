#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

requirements = [
    'Django==3.2',
    'django-auth-ldap==4.1.0',

    'celery==5.2.3',
    'celery-haystack-ng',
    'django-celery-beat==2.3.0',
    'django-celery-results==2.4.0',

    'django-sql-explorer==2.4.1',
    'django-excel-response==2.0.5',
    'xlsxwriter==1.2.9',

    'django-model-utils==4.2.0',
    'django-sequences==2.2',
    'django-enumchoicefield==3.0',

    'django-compressor==2.2',
    'django-debug-toolbar==3.2.0',
    'django-formtools==2.1',
    'django-widget-tweaks==1.4.3',
    'django-countries==7.3.2',
    
    'django-haystack==3.1',
    'django-reversion==3.0.3',
    'django-guardian==2.4.0',
    'django-stronghold==0.3.0',
    
    'gunicorn==19.9.0',
    'ipython==7.16.3',
    'ontobio==2.7',
    'yamldown>=0.1.8',
    'psycopg2-binary==2.9.3',
    'pysolr==3.8.1',
    'pytest-runner==5.1',
    'python-keycloak==0.26.1',
    'pytz==2022.1',
    'requests==2.25.1',
    'urllib3==1.26.5',
    'setuptools-scm==3.3.3',
    'jsonschema==3.2.0',
    'marshmallow==3.17.0'
]

test_requirements = [
    'coverage==5.0a5', 'factory_boy==2.12.0', 'mockldap==0.3.0', 'pytest==7.0.1', 'pytest-django==3.10.0', 'pytest-solr==1.0a1', 'pytest-celery'
]

dev_requirements = [
]

setup(
    name='elixir-daisy',
    version='1.6.0',
    description="Elixir-LU DAISY",
    author="Pinar Alper, Valentin Grouès, Yohan Jarosz, Jacek Lebioda, Kavita Rege, Vilem Ded",
    author_email='lcsb.sysadmins@uni.lu',
    url='https://github.com/elixir-luxembourg/daisy',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_dir={'elixir_daisy':
                     'elixir_daisy'},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords=['elixir', 'gdpr', 'data protection'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.10',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    package_data={
        'elixir-daisy': ['elixir_daisy/resources/*']
    },
    extras_require={
        'dev': dev_requirements
    },
    scripts=['manage.py']
)
