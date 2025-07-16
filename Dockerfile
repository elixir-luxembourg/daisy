FROM python:3.9.6-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    NODE_VERSION=20 \
    DEBIAN_FRONTEND=noninteractive \
    DJANGO_SETTINGS_MODULE=elixir_daisy.settings_compose

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsasl2-dev \
    python3-dev \
    libldap2-dev \
    libssl-dev \
    build-essential \
    git \
    wget \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_VERSION}.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create required directories
RUN mkdir -p /code/log /static && chown -R 1000:1000 /code && chown -R 1000:1000 /static

# Upgrade pip
RUN pip install --upgrade pip


# Install and build npm dependencies
COPY web/static /code/web/static
RUN chown -R 1000:1000 /code/web/static

# Fix npm cache permission
RUN mkdir -p /.npm && chown -R 1000:1000 /.npm

WORKDIR /code/web/static/vendor
USER 1000:1000
RUN npm ci && npm run build

# Set working directory
WORKDIR /code

# Copy dependency files first to leverage Docker caching
COPY setup.py /code/
COPY manage.py /code/

USER root
RUN pip install --no-cache-dir -e .

# Copy the rest of the project files
COPY . /code/
RUN chown -R 1000:1000 /code
# Switch back to /code
WORKDIR /code
USER 1000:1000
RUN python manage.py collectstatic --noinput

USER root
RUN rm -rf /code/web/static
