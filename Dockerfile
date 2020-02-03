FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /code/log /static \
    && apt-get update \
    && apt-get install -yq libsasl2-dev python-dev libldap2-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /code

# Copy the list of Python dependencies
COPY ./setup.py /code/.
# Try to install as many Python dependencies as possible...
RUN pip install -e . 2>/dev/null || true
# ... so that next time the project changes, the previous steps will be cached...
COPY . /code/
# ... and this will be blazing fast
RUN pip install -e .
