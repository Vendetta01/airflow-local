#!/bin/bash

cd airflow/
docker build . \
	--build-arg PYTHON_BASE_IMAGE="python:3.10-slim-buster" \
	--build-arg AIRFLOW_VERSION="2.7.0" \
	--build-arg AIRFLOW_EXTRAS="celery,ldap" \
	-t npodewitz/airflow-minimal:latest
docker tag npodewitz/airflow-minimal:latest npodewitz/airflow-minimal:2.7.0-python3.10

