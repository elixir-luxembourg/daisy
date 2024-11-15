
# Development

## Linting

pip install black==23.7.0
pre-commit install
black --check .
black .

## Import users from active directory

```bash
./manage.py import_users
```

## Import projects, datasets or partners from external system

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

## Install js and css dependencies

```bash
cd web/static/vendor/
npm ci
```

## Compile daisy.scss and React

```bash
cd web/static/vendor
npm run-script build
```

## Run the built-in web server (for development)

```bash
./manage.py runserver
```

## Run the tests

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
