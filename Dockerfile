FROM python:3.9.6-slim
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /code/log /static \
    && apt-get update \
    && apt-get install -yq libsasl2-dev python-dev libldap2-dev git libssl-dev build-essential wget \
    && rm -rf /var/lib/apt/lists/*

# Install node 
RUN apt-get update \
    && apt-get install -y ca-certificates curl gnupg
RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
RUN apt-get update \
    && apt-get install -y nodejs

COPY web/static /static

# Install npm dependencies
RUN cd /static/vendor \
    && npm ci \
    && npm run-script build

WORKDIR /code

RUN pip install --upgrade pip
# Copy the list of Python dependencies
COPY ./setup.py /code/.
# Try to install as many Python dependencies as possible...
RUN pip install --no-cache-dir -e . 2>/dev/null || true
# ... so that next time the project changes, the previous steps will be cached...
COPY . /code/
# ... and this will be blazing fast
RUN pip install --no-cache-dir -e .
