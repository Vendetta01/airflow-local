#!/bin/bash

cd airflow/
docker build . \
	--build-arg PYTHON_BASE_IMAGE="python:3.8-slim-buster" \
	--build-arg AIRFLOW_VERSION="2.2.2" \
	--build-arg AIRFLOW_EXTRAS="celery,ldap" \
	-t npodewitz/airflow-minimal:latest
docker tag npodewitz/airflow-minimal:latest npodewitz/airflow-minimal:2.2.2-python3.8

