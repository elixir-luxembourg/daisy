#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

requirements = [
    'Django==2.2',
    'django-auth-ldap==1.7.0',
    'django-celery-beat==1.4.0',
    'django-celery-results==1.0.4',
    'django-compressor==2.2',
    'django-debug-toolbar==1.11',
    'django-enumchoicefield==1.1.0',
    'django-formtools==2.1',
    'django-guardian==1.5.0',
    'django-haystack==2.8.1',
    'django-reversion==3.0.3',
    'django-stronghold==0.3.0',
    'django-widget-tweaks==1.4.3',
    'django-countries==5.3.3',
    'gunicorn==19.9.0',
    'ipython==7.3.0',
    'libsass==0.17.0',
    'ontobio==1.7.2',
    'yamldown>=0.1.8',
    'psycopg2==2.7.7',
    'pysolr==3.8.1',
    'pytest-runner==5.1',
    'pytz==2018.9',
    'celery==4.3.0',
    'celery-haystack==0.10',
    'setuptools-scm',
    'django-model-utils==3.1.2',
    'django-sequences==2.2'
]

test_requirements = [
    'coverage==5.0a5', 'factory_boy==2.12.0', 'mockldap==0.3.0', 'pytest-django==3.5.1', 'pytest-solr==1.0a1'
]

dev_requirements = [
]

setup(
    name='elixir-daisy',
    version='1.1.0',
    description="Elixir-LU DAISY",
    author="Pinar Alper, Valentin Grouès, Yohan Jarosz, Jacek Lebioda, Kavita Rege",
    author_email='valentin.groues@uni.lu',
    url='https://github.com/elixir-luxembourg/daisy',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_dir={'elixir_daisy':
                     'elixir_daisy'},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords=['elixir', 'gdpr', 'data protection'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        # 'Intended Audience :: Developers',
        # 'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
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
