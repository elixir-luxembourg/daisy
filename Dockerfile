FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN mkdir -p /code/log /static \
    && apt-get update \
    && apt-get install -yq libsasl2-dev python-dev libldap2-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /code
ADD . /code/
#RUN pip install -e ".[dev]" &&  pip install coverage pytest
RUN pip install -e .