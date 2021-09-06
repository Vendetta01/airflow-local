FROM npodewitz/airflow-minimal:2.1.3-python3.8

COPY requirements.txt /home/airflow/requirements.txt
RUN pip install -r /home/airflow/requirements.txt

