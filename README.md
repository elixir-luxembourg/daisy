# Elixir Daisy
![Build Status](https://github.com/elixir-luxembourg/daisy/actions/workflows/main.yml/badge.svg)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-396/)

Data Information System (DAISY) is a data bookkeeping application designed to help Biomedical Research institutions with their GDPR compliance.

For more information, please refer to the official [Daisy documentation](https://elixir.pages.uni.lu/daisy-doc/).

DAISY was published as an article [DAISY: A Data Information System for accountability under the General Data Protection Regulation](https://doi.org/10.1093/gigascience/giz140) in GigaScience journal.

## Demo deployment
You are encouraged to try Daisy for yourself using our [DEMO deployment](https://daisy-demo.elixir-luxembourg.org/).

## Deployment using Docker

### Requirements

* docker: https://docs.docker.com/install/

### Installation

1. Get the source code
    
    ```bash
    git clone git@github.com:elixir-luxembourg/daisy.git
    cd daisy
    ```
1. Create your settings file
    
	```bash
	cp elixir_daisy/settings_local.template.py elixir_daisy/settings_local.py
	```
    Optional: edit the file elixir_daisy/settings_local.py to adapt to your environment.

1. Build daisy docker image  
    ```bash
    docker-compose up --build
    ```
    Wait for the build to finish and keep the process running
1. Open a new shell and go to daisy folder

1. Build the database
    
    ```bash
    docker-compose exec web python manage.py migrate
    ```
1. Build the solr schema

    ```bash
    docker-compose exec web python manage.py build_solr_schema -c /solr/daisy/conf -r daisy -u default
    ```

1. Compile and deploy static files
    
    ```bash
    docker-compose exec web python manage.py collectstatic
    ```
1. Create initial data in the database
    
    ```bash
    docker-compose exec web bash -c "cd core/fixtures/ && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/edda.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hpo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hdo.json && wget https://git-r3lab.uni.lu/pinar.alper/metadata-tools/raw/master/metadata_tools/resources/hgnc.json"
    docker-compose exec web python manage.py load_initial_data
    ```
   Initial data includes, for instance, controlled vocabularies terms and initial list of institutions and cohorts.  
   **This step can take several minutes to complete**
    
1. Load demo data
    
    ```bash
    docker-compose exec web python manage.py load_demo_data
    ```
    This will create mock datasets, projects and create an demo admin account.

1. Optional - import users from an active directory instance

    ```bash
    docker-compose exec web python manage.py import_users
    ```
    
1.  Build the search index

    ```bash
    docker-compose exec web python manage.py rebuild_index -u default
    ```    

1. Browse to https://localhost  
    a demo admin account is available:
    
    ```
        username: admin
        password: demo
    ```

### Operation manual


#### Importing 

In addition to loading of initial data, DAISY database can be populated by importing Project, Dataset and Partners records from JSON files using commands `import_projects`, `import_datasets` and `import_partners` respectively.
 The commands for import are accepting one JSON file (flag `-f`): </br>

```bash
docker-compose exec web python manage.py <COMMAND> -f ${PATH_TO_JSON_FILE}
```
where ${PATH_TO_JSON_FILE} is the path to a json file containing the records definitions.
See file daisy/data/demo/projects.json as an example.
 
Alternatively, you can specify directory containing multiple JSON files to be imported with `-d` flag:
```bash
docker-compose exec web python manage.py <COMMAND> -d ${PATH_TO_DIR}
```

#### Exporting  

Information in the DAISY database can be exported to JSON files. The command for export are given below:</br>

```bash
docker-compose exec web python manage.py export_partners -f ${JSON_FILE}
```
where ${JSON_FILE} is the path to a json file that will be produced.  In addition to ````export_partners````, you can run ````export_projects```` and ````export_datasets```` in the same way.

### Upgrade to last Daisy version

1. Create a database backup.

	```bash
	docker-compose exec db pg_dump daisy --port=5432 --username=daisy --no-password --clean > backup_`date +%y-%m-%d`.sql
	```
	
1. Make sure docker containers are stopped.

	```bash
	docker-compose stop
	```

3. Get last Daisy release.

	```bash
	git checkout master
	git pull
	```

1. Rebuild and start the docker containers.

	```bash
	docker-compose up --build
	```
	Open a new terminal window to execute the following commands.

1. Update the database schema.

	```bash
	docker-compose exec web python manage.py migrate
	```

1. Update the solr schema.

	```bash
	docker-compose exec web python manage.py build_solr_schema -c /solr/daisy/conf -r daisy -u default
	```

1. Collect static files.
 
	```bash
	docker-compose exec web python manage.py collectstatic
	```

	
1. Rebuild the search index.
    
    ```bash
    docker-compose exec web python manage.py rebuild_index -u default
    ```	
1. Reimport the users (optional).
	    
    If LDAP was used during initial setup to import users, they have to be imported again:
    
    ```bash
    docker-compose exec web python manage.py import_users
    ```
    
## Deployment without Docker - CentOS


See [DEPLOYMENT](DEPLOYMENT.md).


## Development

To be completed.

### Import users from active directory
```bash
./manage.py import_users
```

### Import projects, datasets or partners from external system
Single file mode:
```bash
./manage.py import_projects -f path/to/json_file.json
```

Batch mode:
```bash
./manage.py import_projects -d path/to/dir/with/json/files/
```

Available commands: `import_projects`, `import_datasets`, `import_partners`.

In case of problems, add `--verbose` flag to the command, and take a look inside `./log/daisy.log`. 

### Install js and css dependencies

```bash
cd web/static/vendor/
npm ci
```

### Compile daisy.scss
```bash
cd web/static/vendor
npm run-script build
```

### Run the built-in web server (for development)

```bash
./manage.py runserver
```

### Run the tests

The following command will install the test dependencies and execute the tests:

```bash
python setup.py pytest
```

If tests dependencies are already installed, one can also run the tests just by executing:

```bash
pytest
```

To run them in Docker environment, build and run the containers (`docker-compose up --build`), and execute:

```bash
docker-compose exec web python setup.py pytest
```

## Administration

To get access to the admin page, you must log in with a superuser account.  
On the `Users` section, you can give any user a `staff` status and he will be able to access any project/datasets.


## `settings.py` and `local_settings.py` reference

### Display
| Key | Description | Expected values | Example value |
|---|---|---|---|
| `COMPANY` | A name that is used to generate verbose names of some models | str | `'LCSB'` |
| `DEMO_MODE` | A flag which makes a simple banneer about demo mode appear in About page | bool | `False` | 
| `INSTANCE_LABEL` | A name that is used in navbar header to help differentiate different deployments | str | `'Staging test VM'` | 
| `INSTANCE_PRIMARY_COLOR` | A color that will be navbar header's background | str of a color | `'#076505'` | 
| `LOGIN_USERNAME_PLACEHOLDER` | A helpful placeholder in login form for logins | str | `'@uni.lu'` | 
| `LOGIN_PASSWORD_PLACEHOLDER` | A helpful placeholder in login form for passwords | str | `'Hint: use your AD password'` | 

### Integration with other tools
#### ID Service
| Key | Description | Expected values | Example value |
|---|---|---|---|
| `IDSERVICE_FUNCTION` | Path to a function (`lambda: str`) that generates IDs for entities which are published | str | `'web.views.utils.generate_elu_accession'` |
| `IDSERVICE_ENDPOINT` | In case LCSB's idservice function is being used, the setting contains the IDservice's URI | str | `'https://192.168.1.101/v1/api/` |

#### REMS
| Key | Description | Expected values | Example value |
|---|---|---|---|
| `REMS_INTEGRATION_ENABLED` | A feature flag for REMS integration. In practice, there's a dedicated endpoint which processes the information from REMS about dataset entitlements | str | `True` |
| `REMS_SKIP_IP_CHECK` | If set to `True`, there will be no IP checking if the request comes from trusted REMS instance. | bool | `False` |
| `REMS_ALLOWED_IP_ADDRESSES` | A list of IP addresses that should be considered trusted REMS instances. Beware of configuration difficulties when using reverse proxies. The check can be skipped with `REMS_SKIP_IP_CHECK` | dict[str] | `['127.0.0.1', '192.168.1.101']` |

#### Keycloak
| Key | Description | Expected values | Example value |
|---|---|---|---|
| `KEYCLOAK_INTEGRATION` | A feature flag for importing user information from Keycloak (OIDC IDs) | bool | `True` |
| `KEYCLOAK_URL` | URL to the Keycloak instance | str | `'https://keycloak.lcsb.uni.lu/auth/'` |
| `KEYCLOAK_REALM_LOGIN` | Realm's login name in your Keycloak instance | str | `'master'` |
| `KEYCLOAK_REALM_ADMIN` | Realm's admin name in your Keycloak instance | str | `'master'` |
| `KEYCLOAK_USER` | Username to access Keycloak | str | `'username'` |
| `KEYCLOAK_PASS` | Password to access Keycloak | str | `'secure123'` |

### Others
| Key | Description | Expected values | Example value |
|---|---|---|---|
| `SERVER_SCHEME` | A URL's scheme to access your DAISY instance (http or https) | str | `'https'` |
| `SERVER_URL` | A URL to access your DAISY instance (without the scheme) | str | `'example.com'` |
| `GLOBAL_API_KEY` | An API key that is not connected with any user. Disabled if set to `None` | optional[str] | `'in-practice-you-dont-want-to-use-it-unless-debugging'` |