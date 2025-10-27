# Development

## Environment Setup

DAISY loads configuration from `.env.{ENVIRONMENT}` files:

- `.env.development` (default, works with Docker)
- `.env.local` (for local development outside Docker)
- `.env.test` (testing)

**For local development:**

```bash
cp .env.development .env.local
# Edit .env.local: set ENVIRONMENT=local, adjust DATABASE_URL/SOLR_URL for localhost
```

See [administration.md](administration.md#environment-variables-reference) for all settings.

## Linting

pip install black==25.1.0
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

Install test dependencies:

```bash
pip install ".[test]"
```

If tests dependencies are already installed, one can also run the tests just by executing:

```bash
pytest
```

## Docker Development Setup

DAISY includes Docker Compose configurations for both production and development environments.

### Development Setup

For development with live file mounting and automatic updates:

```bash
# Stop any running containers
docker compose down

# Start with development overrides
docker compose -f docker-compose.yaml -f docker-compose.dev.yml up
```

The development setup provides:

- **Live static file mounting**: Changes to CSS/JS files are immediately available
- **Hot reload**: Code changes are reflected without rebuilding containers

### Compiling Assets in Docker

When you make changes to SCSS files, compile them using:

```bash
# Compile SCSS to CSS
docker compose -f docker-compose.yaml -f docker-compose.dev.yml exec web bash -c "cd /static/vendor && npm run build:css"

# Build all assets (CSS + JavaScript)
docker compose -f docker-compose.yaml -f docker-compose.dev.yml exec web bash -c "cd /static/vendor && npm run build"

# Watch for SCSS changes (auto-compile on file changes)
docker compose -f docker-compose.yaml -f docker-compose.dev.yml exec web bash -c "cd /static/vendor && npm run watch:css"
```

### Installing Dependencies in Docker

```bash
# Install npm dependencies
docker compose -f docker-compose.yaml -f docker-compose.dev.yml exec web bash -c "cd /static/vendor && npm ci"

# Collect Django static files
docker compose -f docker-compose.yaml -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput
```

### Testing in Docker

```bash
docker compose exec --user root web pip install ".[test]"
docker compose exec web pytest
```
