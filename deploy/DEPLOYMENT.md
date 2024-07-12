# Deployement

In order to install the tool, you can use Ansible or Docker deployement.

- Docker deployment for demos or development
- Ansible deployment for production

## Initialization

Additional manual setup is required to customize the deployment to your infrastructure.

### Local configuration file

```bash
sudo su - daisy
cp /home/daisy/daisy/elixir_daisy/settings_local.template.py   /home/daisy/daisy/elixir_daisy/settings_local.py
vi /home/daisy/daisy/elixir_daisy/settings_local.py
```

<span style="color:red;">Change SECRET_KEY variable:</span>

```
# SECURITY WARNING: change the secret key used in production and keep it secret !
SECRET_KEY='<your-new-secret-key>'
```

Put in the following database configuration to the 'settings_local.py' file.

```
#......
#......
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'daisy',
        'USER': 'daisy',
        'PASSWORD': 'daisy',
        'HOST': 'localhost',
        'PORT': 5432
    }
}
#......
#......
```

Put in the following haystack configuration to the 'settings_local.py' file.

```
#......
#......
HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
            'URL': 'http://127.0.0.1:8983/solr/daisy',
            'ADMIN_URL': 'http://127.0.0.1:8983/solr/admin/cores',
        },
}
HAYSTACK_SIGNAL_PROCESSOR = 'celery_haystack.signals.CelerySignalProcessor'
#......
#......
```
Add the following entries:
```
STATIC_ROOT = "/home/daisy/static/"
ALLOWED_HOSTS = ['10.x.x.x','daisy.com']
DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

Please note that the IP and DNS record should be CHANGED to denote your server.

Replace the company name 'LCSB' with your institution name.
We suggest that you use a not very long name here e.g. the acronym of your institution.

If needed, configure the active directory parameters to allow LDAP authentication and user imports. 
Exit the daisy user.
```bash
exit
```

### Initial data

Once everything is set up, the definitions and lookup values need to be inserted into the database.
To do this run the following.

```bash
sudo su - daisy
cd /home/daisy/daisy
python3.9 manage.py collectstatic 
python3.9 manage.py migrate 
python3.9 manage.py build_solr_schema -c /var/solr/data/daisy/conf -r daisy  
cd /home/daisy/daisy/core/fixtures/
wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/edda.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hpo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hdo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hgnc.json
cd /home/daisy/daisy
python3.9 manage.py load_initial_data
```

### Demo data - optional

The load_initial_data command needs several minutes to complete.
DAISY has a demo data loader. With example records of Projects Datasets and Users. If you want to deploy DAISY  demo data, then do 

```bash
python3.9 manage.py load_demo_data
```

The above command will create an 'admin' and other users such as 'alice.white', 'john.doe' 'jane.doe'. The password for all  is 'demo'.

### Import users

If you do not want to load the demo data and work with your own definitions, then you'd still need to create super user for the application, with which you can logon and create other users as well as records. To create a super user, do the following and respond to the questions. 

```bash
python3.9 manage.py createsuperuser
```

Trigger a reindex with:

```bash
python3.9 manage.py rebuild_index
```

## Validate the installation

Check the the installation was successful by accessing the URL `https://${IP_OF_THE_SERVER}` with a web browser.
You should be able to login with `admin/demo` if the `load_demo_data` command was used or with your own admin account if the `createsuperuser` command was used.
It should be possible to create datasets and projects.

In addition when the DAISY is updated or configurations are changed (including the configuration files such as ```settings_local.py```) is modified, gunicorn must be restarted to load the new code/configuration, to do so run:

```bash
sudo systemctl restart gunicorn
sudo systemctl restart celery_worker
sudo systemctl restart celery_beat
```
## Updating DAISY

If you want to move to the newest release of DAISY, do the following.  

1) Stop services, create a database and application backup.

As root user:

```bash
systemctl stop gunicorn
systemctl stop celery_worker
systemctl stop celery_beat 
su -c 'PGPASSWORD="<PASSWORD_OF_POSTGRES_USER>" pg_dump daisy --port=5432 --username=daisy --clean > daisy_dump.sql' - daisy 
tar -cvf /tmp/daisy.tar /home/daisy 
```

Once you have have created the tar ball of the application directory and the postgres dump, then you may proceed to update.

2) Get the latest Daisy release.

As daisy user:

```bash
cd /home/daisy/daisy
git checkout -- web/static/vendor/package-lock.json
git checkout master
git pull


cd /home/daisy/daisy/web/static/vendor/
npm ci
```

As root user:

```bash
/usr/local/bin/pip3.9 install -e /home/daisy/daisy --upgrade
```

3) Update the database and solr schemas, collect static files.

As daisy user:

```bash
cd /home/daisy/daisy
python3.9 manage.py migrate && python3.9 manage.py build_solr_schema -c /var/solr/data/daisy/conf/ -r daisy && yes | python3.9 manage.py clear_index && yes "yes" | python3.9 manage.py collectstatic;
```

4) Reload initial data (optional).


**IMPORTANT NOTE:** The initial data package provides some default values for various lookup lists e.g. data sensitivity classes, document or data types.  If, while using DAISY, you have customized these default lists, please keep in mind that running the ``load_initial_data`` command
during update will re-introduce those default values. If this is not desired, then please skip the reloading of initial data step during your update. You manage lookup lists through the application interface.<br/><br/>

As daisy user:

```bash
cd /home/daisy/daisy/core/fixtures/
wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/edda.json -O edda.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hpo.json -O hpo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hdo.json -O hdo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hgnc.json -O hgnc.json

cd /home/daisy/daisy
python3.9 manage.py load_initial_data
```
  
**IMPORTANT NOTE:** This step can take several minutes to complete.

5) Reimport the users (optional).

If LDAP was used to import users, they have to be imported again.
As daisy user:
```bash
python3.9 manage.py import_users
```

6) Rebuild Solr search index.

As daisy user:
 ```bash
 cd /home/daisy/daisy
 python3.9 manage.py rebuild_index
```

7) Restart services.

As root user:

```bash
systemctl start gunicorn
systemctl start celery_worker
systemctl start celery_beat 
```

## Restoring backup of Daisy
First, make sure you have successfully backed up your Daisy deployment - see first section of chapter Updating Daisy.
Your backup .tar file should contain both the dump of Postgresql database and everything from `/home/daisy` directory.

As root user, stop services:
```bash
systemctl stop gunicorn
systemctl stop celery_worker
systemctl stop celery_beat
```

Wipe out broken/unwanted version of Daisy by deleting all files in daisy user home directory and dropping the database:  
**IMPORTANT NOTE**: Be sure that your backup .tar file is stored somewhere else!
```
rm -rf /home/daisy/*
su -c 'dropdb daisy' - postgres
```

Restore files from tar ball:
```
su -c 'tar -xvf <PATH-TO-BACKUP-FOLDER>/daisy.tar --directory /' - daisy
```

Following steps assume that the Postgresql10 is installed, pg_hba.conf file is updated and database user *daisy* exists (please see the postgresql deployment instructions for more information).
Create the database and grant privileges:
```
su - postgres
createdb daisy
psql -d daisy -p 5432 -c "grant all privileges on database daisy to daisy"
exit
```

Restore the database as daisy user: 
```
su -c 'psql -d daisy -U daisy -p 5432 < /home/daisy/daisy_dump.sql' - daisy
```

Start services: 
```
systemctl start gunicorn
systemctl start celery_worker
systemctl start celery_beat 
```

## Migration

### Daisy 1.7.12 to 1.8.0

The migration introduced breaking change and update of `settings.py` file is required. The new scheduled tasks as defined in [settings_template.py](https://github.com/elixir-luxembourg/daisy/blob/de64e17355700dc029133f48a295be82341486ed/elixir_daisy/settings_local.template.py#L91) must be included to fully support new features.

Update of nodejs is required:

```bash
curl -sL https://rpm.nodesource.com/setup_16.x | sudo bash -
sudo yum install nodejs
```

### Daisy 1.7.0 to 1.7.1
The migration introduced breaking change by updating python-keycloak to version `2.6.0`. If you are using Keycloak integration, update your `elixir_daisy/settings_local.py` file to contain **all** Keyclock related variables defined in README Keycloak [section](https://github.com/elixir-luxembourg/daisy/blob/master/README.md#keycloak).

### DAISY 1.6.0 to 1.7.0
 * Due to the change of Celery to 5.X, you must update Celery service definitions. Please take a look on Celery section in this document and make sure the content of your Celery config files matches the content here (only the order of parameters has changed).
 * Python version was migrated from 3.6 to 3.9 - new python and pip version need to be installed (see section **Base** of deployment instructions)
