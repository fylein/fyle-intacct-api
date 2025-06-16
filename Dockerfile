# Pull python base image
FROM python:3.10-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y install libpq-dev gcc && apt-get install git postgresql-client curl -y --no-install-recommends

# Installing requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -U pip wheel setuptools && pip install -r /tmp/requirements.txt && pip install pylint-django==2.3.0

# Copy Project to the container
RUN mkdir -p /fyle-intacct-api
COPY . /fyle-intacct-api/
WORKDIR /fyle-intacct-api

# Do linting checks
# RUN flake8 .

ARG SERVICE_GID=1001

#================================================================
# Setup non-root user and permissions
#================================================================
RUN groupadd -r -g ${SERVICE_GID} intacct_api_service && \
    useradd -r -g intacct_api_service intacct_api_user && \
    chown -R intacct_api_user:intacct_api_service /fyle-intacct-api

# Switch to non-root user
USER intacct_api_user

# Expose development port
EXPOSE 8000

# Run development server
CMD /bin/bash run.sh
