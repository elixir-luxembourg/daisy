# Installation

## Base

```bash
sudo yum update
sudo yum install python36-devel openldap-devel nginx
sudo yum group install "Development Tools"

wget https://bootstrap.pypa.io/get-pip.py
sudo python36 get-pip.py
```



# User and Application Source Code

We install the application under a dedicated `daisy` user.

```bash
sudo useradd daisy
sudo usermod -a -G users daisy
sudo su - daisy
mkdir config log
git clone https://github.com/elixir-luxembourg/daisy.git
exit
sudo /usr/local/bin/pip install -e /home/daisy/daisy
sudo /usr/local/bin/pip install gunicorn
```

## NPM and Node.js

```bash
curl -sL https://rpm.nodesource.com/setup_10.x | sudo bash -
sudo yum install nodejs
```

Then you need to compile the static files.


```bash
sudo su - daisy
cd /home/daisy/daisy/web/static/vendor/
npm ci
exit
```


## Solr

```bash
sudo useradd solr
wget https://archive.apache.org/dist/lucene/solr/7.7.1/solr-7.7.1.tgz
tar -xf solr-7.7.1.tgz solr-7.7.1/bin/install_solr_service.sh
sudo yum install lsof java-1.8.0-openjdk
sudo solr-7.7.1/bin/install_solr_service.sh solr-7.7.1.tgz
sudo su - solr
/opt/solr-7.7.1/bin/solr create_core -c daisy
cd /var/solr/data/daisy/conf
wget "https://raw.githubusercontent.com/apache/lucene-solr/master/solr/example/files/conf/currency.xml"  
wget "https://raw.githubusercontent.com/apache/lucene-solr/master/solr/example/files/conf/elevate.xml"  
/opt/solr-7.7.1/bin/solr stop  
exit
```
It is possible that by this time solr-7.7.1 is not anymore proposed for download on solr mirrors.
In this case check for last solr version available and adapt the instructions above accordingly.
You need configure the solr core 'daisy'. To do so you need to create 'schema.xml' and 'solrconfig.xml' files under 
'/var/solr/data/daisy/conf'. 
```bash
sudo cp /home/daisy/daisy/docker/solr/schema.xml /var/solr/data/daisy/conf/
sudo cp /home/daisy/daisy/docker/solr/solrconfig.xml /var/solr/data/daisy/conf/
sudo chown -R solr:users /var/solr
sudo chmod -R 775 /var/solr
```

<span style="color:red;">Review the 'schema.xml' file you just copied. Ensure that all file references inside it (e.g. stopwords.txt) actually exist in the path specified.</span>

<p style="color:red;">By default, the Solr instance listens on port 8983 on all interfaces.
Solr has no authentication system. It is crucial to secure it by either blocking external accesses to the Solr port or by changing it's configuration to listen only on localhost (see https://stackoverflow.com/a/1955591)</p>


You can restart solr and check that it is working with the following commands

```bash
sudo systemctl enable solr
sudo systemctl restart solr
```

## Gunicorn

1) Create the file ```/etc/systemd/system/gunicorn.service``` as the _root_ user or with _sudo_ and with the following content:


```
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
PIDFile=/run/gunicorn/pid
User=daisy
Group=daisy
WorkingDirectory=/home/daisy/daisy
ExecStart=/usr/local/bin/gunicorn --limit-request-line 0 --access-logfile /home/daisy/log/gunicorn_access.log --error-logfile /home/daisy/log/gunicorn_error.log --log-level debug --workers 2 --bind unix:/home/daisy/daisy/daisy.sock elixir_daisy.wsgi
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM  $MAINPID

[Install]
WantedBy=multi-user.target
```

## Rabbitmq

```bash
sudo yum install rabbitmq-server  
sudo systemctl start rabbitmq-server  
sudo systemctl enable gunicorn  
```

## Celery

We use systemd to create two services, celery_worker to run the worker (notifications, indexation, etc) and celery_beat to run the scheduled tasks.

1) Celery worker

As daisy user, create the file /home/daisy/config/celery.conf with the following content:

```
# Name of nodes to start
# here we have a single node
CELERYD_NODES="daisy_worker"
# or we could have three nodes:
#CELERYD_NODES="w1 w2 w3"

# Absolute or relative path to the 'celery' command:
CELERY_BIN="/usr/local/bin/celery"
#CELERY_BIN="/virtualenvs/def/bin/celery"

# App instance to use
# comment out this line if you don't use an app
CELERY_APP="elixir_daisy.celery_app"
# or fully qualified:
#CELERY_APP="proj.tasks:app"

# How to call manage.py
CELERYD_MULTI="multi"

# Extra command-line arguments to the worker
CELERYD_OPTS="--concurrency=1"

# - %n will be replaced with the first part of the nodename.
# - %I will be replaced with the current child process index
#   and is important when using the prefork pool to avoid race conditions.
CELERYD_PID_FILE="/var/run/celery/%n.pid"
CELERYD_LOG_FILE="/home/daisy/log/celery/%n%I.log"
CELERYD_LOG_LEVEL="DEBUG"
```

Create the  folders '/var/run/celery/' as _root_ or with _sudo_ and the folder '/home/daisy/log/celery' as _daisy_ must be created. 
Create also the service config file '/etc/systemd/system/celery_worker.service' as _root_ or with _sudo_ and with the following content:

```
[Unit]
Description=Celery Worker
After=network.target

[Service]
Type=forking
User=daisy
Group=daisy
EnvironmentFile=/home/daisy/config/celery.conf
WorkingDirectory=/home/daisy/daisy
ExecStart=/bin/sh -c '${CELERY_BIN} multi start ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'
ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait ${CELERYD_NODES} \
  --pidfile=${CELERYD_PID_FILE}'
ExecReload=/bin/sh -c '${CELERY_BIN} multi restart ${CELERYD_NODES} \
  -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} \
  --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'

[Install]
WantedBy=multi-user.target
```

Then do the following:

```bash
sudo systemctl enable celery_worker  
sudo systemctl start celery_worker  
```

2) Celery beat

Create the file /home/daisy/config/celerybeat.conf with the following content:

```
# Absolute or relative path to the 'celery' command:
CELERY_BIN="/usr/local/bin/celery"

# App instance to use
# comment out this line if you don't use an app
CELERY_APP="elixir_daisy.celery_app"
# or fully qualified:
#CELERY_APP="proj.tasks:app"

# Extra command-line arguments to the worker
CELERYBEAT_OPTS="--scheduler django_celery_beat.schedulers:DatabaseScheduler"

# - %n will be replaced with the first part of the nodename.
# - %I will be replaced with the current child process index
#   and is important when using the prefork pool to avoid race conditions.
CELERYBEAT_PID_FILE="/var/run/celerybeat/%n.pid"
CELERYBEAT_LOG_FILE="/home/daisy/log/celerybeat/%n%I.log"
CELERYBEAT_LOG_LEVEL="INFO"
```

Create the service file /etc/systemd/system/celery_beat.service:

```
[Unit]
Description=Celery Beat Service
After=network.target

[Service]
User=daisy
Group=daisy
EnvironmentFile=/home/daisy/config/celerybeat.conf
WorkingDirectory=/home/daisy/daisy
ExecStart=/bin/sh -c '${CELERY_BIN} beat -A ${CELERY_APP} --pidfile=${CELERYBEAT_PID_FILE} \
  --logfile=${CELERYBEAT_LOG_FILE} --loglevel=${CELERYBEAT_LOG_LEVEL} ${CELERYBEAT_OPTS}'
ExecStop=/bin/kill -s TERM $MAINPID

[Install]
WantedBy=multi-user.target 
```

Then do the following:

```bash
sudo systemctl enable celery_beat 
sudo systemctl start celery_beat  
```

## PostgreSQL

### Install database server

Documentation from: https://www.postgresql.org/download/linux/redhat/

```bash
sudo yum install https://download.postgresql.org/pub/repos/yum/10/redhat/rhel-7-x86_64/pgdg-centos10-10-2.noarch.rpm
sudo yum install postgresql10
sudo yum install postgresql10-server
sudo /usr/pgsql-10/bin/postgresql-10-setup initdb
sudo systemctl enable postgresql-10
sudo systemctl start postgresql-10
```

### Create database and roles


```bash
sudo su - postgres
vi ./10/data/pg_hba.conf
```
Change METHOD ident of IPv4 and IPv6 to md5 and add rule for daisy and postgres users.
We recommend to only allow local connection from the daisy user to the daisy database.  
Example:  
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
# "local" is for Unix domain socket connections only
local   daisy           daisy                                   ident
local   postgres        postgres                                ident
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
# IPv6 local connections:
host    all             all             ::1/128                 md5
```

Create daisy user and database:
```
createuser daisy
createdb daisy
psql
postgres=# alter user daisy with encrypted password 'daisy';
postgres=# grant all privileges on database daisy to daisy ;
postgres=# \q
exit
```
<span style="color:red;">You can replace password `daisy` by a password of your choice.</span>

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql-10
```

# Application Config File
Create a local configuration file for the application.

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
# Web server

1) Install nginx

    ```bash
    sudo yum install epel-release
    sudo yum install nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx
    ```
    
2) As _root_ or with _sudo_ create the file ```/etc/nginx/conf.d/ssl.conf``` with the following content:
	   
    ```bash
    proxy_connect_timeout       600;
    proxy_send_timeout          600;
    proxy_read_timeout          600;
    send_timeout                600;
    
    server {
        server_name daisy.com;
    
        location /static {
            alias /home/daisy/static;
            autoindex on;
        }
        
        location / {
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_pass http://unix:/home/daisy/daisy/daisy.sock;
        }
        listen 443 http2 ssl;
        listen [::]:443 http2 ssl;
        ssl on;
        ssl_certificate /etc/ssl/certs/daisy.com.crt;
        ssl_certificate_key /etc/ssl/private/daisy.com.key;
    }
	```    
    
	Changing daisy.com to your particular case.  
    
3) To have a redirect from http to https, as _root_ or with _sudo_ create the file ```/etc/nginx/conf.d/daisy.conf``` with the following content:

    ```
    server {
      listen 80;
      server_name daisy.com;
      return 301 https://daisy.com$request_uri;
    }
    ```
    Changing daisy.com to your particular case.
    
4) Create self-signed certificates if they already don't exist.

    ```bash
    openssl req -x509 -newkey rsa:4096 -nodes -out daisy.com.crt -keyout daisy.com.key -days 365
    ```
    Changing daisy.com to your particular case.
    Certificates should be put in the folder specified in ```/etc/nginx/conf.d/daisy.conf```
    ```bash
    sudo cp daisy.com.crt /etc/ssl/certs/
    sudo mkdir /etc/ssl/private/
    sudo cp daisy.com.key /etc/ssl/private/
 
    ```
5) Edit the file /etc/nginx/nginx.conf:

    Comment out the block server {} in /etc/nginx/nginx.conf
    Change the user running nginx from nginx to daisy
    
6) Grant access on `/var/lib/nginx` to **daisy** user:
   ```
   sudo chown -R daisy:daisy /var/lib/nginx
   ```
   
7) Restart nginx

    ```bash
    sudo systemctl restart nginx
    ```

# Initialization

Once everything is set up, the definitions and lookup values need to be inserted into the database.   
To do this run the following.

```bash
sudo su - daisy
cd /home/daisy/daisy
python36 manage.py collectstatic 
python36 manage.py migrate 
python36 manage.py build_solr_schema -c /var/solr/data/daisy/conf -r daisy  
cd /home/daisy/daisy/core/fixtures/
wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/edda.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hpo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hdo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hgnc.json
cd /home/daisy/daisy
python36 manage.py load_initial_data
```
The load_initial_data command needs several minutes to complete.
DAISY has a demo data loader. With example records of Projects Datasets and Users. If you want to deploy DAISY  demo data, then do 

```bash
python36 manage.py load_demo_data
```

The above command will create an 'admin' and other users such as 'alice.white', 'john.doe' 'jane.doe'. The password for all  is 'demo'.


If you do not want to load the demo data and work with your own definitions, then you'd still need to create super user for the application, with which you can logon and create other users as well as records. To create a super user, do the following and respond to the questions. 

```bash
python36 manage.py createsuperuser
```

Trigger a reindex with:

```bash
python36 manage.py rebuild_index
```

# Validate the installation

Check the the installation was successful by accessing the URL `https://${IP_OF_THE_SERVER}` with a web browser.
You should be able to login with `admin/demo` if the `load_demo_data` command was used or with your own admin account if the `createsuperuser` command was used.
It should be possible to create datasets and projects.

In addition when the DAISY is updated or configurations are changed (including the configuration files such as ```settings_local.py```) is modified, gunicorn must be restarted to load the new code/configuration, to do so run:

```bash
sudo systemctl restart gunicorn
sudo systemctl restart celery_worker
sudo systemctl restart celery_beat
```

# Setting up reminders 

DAISY can generate reminders on approaching deadlines (e.g. data storage end date or document expiry). To enable this feature, do the following:

 1) Login to DAISY as a super user. e.g. `admin` user in the demo application
 
 2) Go to https://${IP_OF_THE_SERVER}/admin
 
 3) From the 'Site administration' list select 'Periodic tasks' under 'PERIODIC TASKS' heading.
 
 4) Clicking the 'ADD PERIODIC TASK' button, then:
    4.1) Give your task a name, 
    4.2) From the 'Task(registered)' list select `notification.tasks.document_expiry_notifications`,
    4.3) From the 'Interval' list select `every day`. If this interval does not exist, you may create it by clicking the (+) button next to the select,.
    4.4) Select a start date and time, e.g. today and now,
    4.5) Click 'SAVE'.
    
 5) You may repeat the steps in (4) to create a daily periodic task also for `notification.tasks.data_storage_expiry_notifications`,
 
# Updating DAISY


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
/usr/local/bin/pip install -e /home/daisy/daisy --upgrade
```

3) Update the database and solr schemas, collect static files.

As daisy user:

```bash
cd /home/daisy/daisy
python36 manage.py migrate && python36 manage.py build_solr_schema -c /var/solr/data/daisy/conf/ -r daisy && yes | python36 manage.py clear_index && yes "yes" | python36 manage.py collectstatic;
```


4) Reload initial data (optional). 


**IMPORTANT NOTE:** The initial data package provides some default values for various lookup lists e.g. data sensitivity classes, document or data types.  If, while using DAISY, you have customized these default lists, please keep in mind that running the ``load_initial_data`` command
during update will re-introduce those default values. If this is not desired, then please skip the reloading of initial data step during your update. You manage lookup lists through the application interface.<br/><br/>
        
As daisy user:
```bash
cd /home/daisy/daisy/core/fixtures/
wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/edda.json -O edda.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hpo.json -O hpo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hdo.json -O hdo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hgnc.json -O hgnc.json

cd /home/daisy/daisy
python36 manage.py load_initial_data
```     
  
**IMPORTANT NOTE:** This step can take several minutes to complete. 


5) Reimport the users (optional).

If LDAP was used to import users, they have to be imported again.
As daisy user:
```bash
python36 manage.py import_users
```

6) Rebuild Solr search index.

As daisy user:
 ```bash
 cd /home/daisy/daisy
 python36 manage.py rebuild_index
```

7) Restart services.

As root user:

```bash
systemctl start gunicorn
systemctl start celery_worker
systemctl start celery_beat 
```
# Restoring backup of Daisy
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
