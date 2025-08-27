FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_VERSION=20 \
    DEBIAN_FRONTEND=noninteractive \
    DJANGO_SETTINGS_MODULE=elixir_daisy.settings_compose

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    # LDAP dependencies
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    # Build tools
    build-essential \
    python3-dev \
    pkg-config \
    # Git and utilities
    git \
    wget \
    curl \
    ca-certificates \
    gnupg \
    # Additional dependencies that might be needed
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (using more efficient method)
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user early
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# Create required directories with proper permissions
RUN mkdir -p /code/log /static /.npm /solr/daisy/conf \
    && chown -R appuser:appuser /code /static /.npm /solr \
    && chmod -R 755 /solr

# Set working directory
WORKDIR /code

# Copy dependency files first (better caching)
COPY --chown=appuser:appuser setup.py requirements.txt* ./
COPY --chown=appuser:appuser manage.py ./

# Upgrade pip and install Python dependencies as root (for system-wide packages)
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -e .

# Copy frontend assets and package files
COPY --chown=appuser:appuser web/static /code/web/static
COPY --chown=appuser:appuser package*.json /code/

# Set npm cache directory and permissions
RUN mkdir -p /home/appuser/.npm \
    && chown -R appuser:appuser /home/appuser/.npm

# Switch to non-root user for npm operations
USER appuser
WORKDIR /code

# Install and build npm dependencies
RUN if [ -f "package.json" ]; then \
    npm ci --omit=dev && \
    npm run build && \
    npm cache clean --force; \
    fi

# Switch back to /code and copy remaining files
WORKDIR /code
COPY --chown=appuser:appuser . .

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Clean up build artifacts to reduce image size
USER root

# Copy the rest of the project files
COPY . /code/
RUN chown -R 1000:1000 /code
# Switch back to /code
WORKDIR /code

RUN apt-get remove -y build-essential python3-dev pkg-config \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && rm -rf /code/web/static/vendor/node_modules

# Switch back to non-root user for runtime
# USER appuser
