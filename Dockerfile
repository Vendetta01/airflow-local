FROM npodewitz/airflow-minimal:2.1.3-python3.8

COPY requirements.txt /home/airflow/requirements.txt
RUN pip install -r /home/airflow/requirements.txt

COPY chromedriver /usr/local/bin/

USER root
RUN apt-get update \
    && apt-get install -y \
    libglib2.0 \
    libnss3 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*
# TODO: Do we still need to install the above?
# I guess it will be installed with chrome anyway???
RUN cd /tmp \
    && curl https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O \
    && apt-get update \
    && apt-get install -y /tmp/google-chrome-stable_current_amd64.deb \
    && rm -f /tmp/google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

USER airflow
