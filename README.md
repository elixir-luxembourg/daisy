# Elixir Daisy
![Build Status](https://github.com/elixir-luxembourg/daisy/actions/workflows/main.yml/badge.svg)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-396/)

Data Information System (DAISY) is a data bookkeeping application designed to help Biomedical Research institutions with their GDPR compliance.

For more information, please refer to the official [Daisy documentation](https://elixir.pages.uni.lu/daisy-doc/).

DAISY was published as an article [DAISY: A Data Information System for accountability under the General Data Protection Regulation](https://doi.org/10.1093/gigascience/giz140) in GigaScience journal.

## Demo

You are encouraged to try DAISY for yourself using our public [DEMO deployment](https://daisy-demo.elixir-luxembourg.org/).

## Deployment

- [Demo and development deployment using Docker](deploy/docker/deployment-using-docker.md)
- [Production deployment using Ansible (Rocky 8)](deploy/ansible/deployment-using-ansible.md)

More information on deployment can be found [here](deploy/DEPLOYMENT.md)

### Operation manual

Following commands are only for docker deployment. In case you used Ansible, the commands have to be run directly in `shell`.

#### Importing records

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

#### Exporting records

Information in the DAISY database can be exported to JSON files. The command for export are given below:</br>

```bash
docker-compose exec web python manage.py export_partners -f ${JSON_FILE}
```
where ${JSON_FILE} is the path to a json file that will be produced.  In addition to ````export_partners````, you can run ````export_projects```` and ````export_datasets```` in the same way.

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

## Development

To be completed.

### Linting

pip install black==23.7.0
pre-commit install
black --check .
black .

### Install js and css dependencies

```bash
cd web/static/vendor/
npm ci
```

### Compile daisy.scss and React
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
run test for a specific file:
```bash
python setup.py pytest --addopts web/tests/test_dataset.py
```

If tests dependencies are already installed, one can also run the tests just by executing:

```bash
pytest
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

External record ID generator can be added. DAISY will use its internal method to generate ID otherwise.

| Key | Description | Expected values | Example value |
|---|---|---|---|
| `IDSERVICE_FUNCTION` | Path to a function (`lambda: str`) that generates IDs for entities which are published | str | `'web.views.utils.generate_elu_accession'` |
| `IDSERVICE_ENDPOINT` | In case LCSB's idservice function is being used, the setting contains the IDservice's URI | str | `'https://192.168.1.101/v1/api/` |

#### REMS

Integrating REMS allows the access objects to be created in DAISY automatically after approval is given.

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