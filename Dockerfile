FROM apache/airflow:slim-2.7.0-python3.10


USER root

# Installing chrome and chromedriver
RUN curl -q https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get -y update \
    && apt-get install -y \
    build-essential \
    google-chrome-stable \
    libpoppler-cpp-dev \
    pkg-config \
    unzip
    

COPY chromedriver-linux64.zip /home/airflow/
RUN unzip -j /home/airflow/chromedriver-linux64.zip chromedriver-linux64/chromedriver -d /usr/local/bin/

COPY requirements.txt /home/airflow/requirements.txt
RUN sudo -u airflow pip install -r /home/airflow/requirements.txt

RUN apt-get remove -y --autoremove \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set display port as an environment variable
ENV DISPLAY=:99

RUN usermod -u 100001 airflow \
    && groupadd -g 965 docker \
    && usermod -aG docker airflow

USER airflow
