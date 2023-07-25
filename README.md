# Elixir Daisy
![Build Status](https://github.com/elixir-luxembourg/daisy/actions/workflows/main.yml/badge.svg)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-396/)

Data Information System (DAISY) is a data bookkeeping application designed to help Biomedical Research institutions with their GDPR compliance.

For more information, please refer to the official [Daisy documentation](https://elixir.pages.uni.lu/daisy-doc/).

DAISY was published as an article [DAISY: A Data Information System for accountability under the General Data Protection Regulation](https://doi.org/10.1093/gigascience/giz140) in GigaScience journal.

## Demo
You are encouraged to try Daisy for yourself using our [DEMO deployment](https://daisy-demo.elixir-luxembourg.org/).

## Deployment

See the following documentation for:

- [Deployment steps on CentOS](deploy/DEPLOYMENT.md)
- [Deployment using Docker](deploy/docker/deployment-using-docker.md)
- [Deployment using Ansible](deploy/ansible/deployment-using-ansible.md)

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