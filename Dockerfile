FROM npodewitz/airflow-minimal:2.1.3-python3.8

ENV CHROME_VERSION=92.0.4515.107


USER root

# Installing chrome and chromedriver
COPY requirements.txt /home/airflow/requirements.txt
RUN curl -q https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get -y update \
    && apt-get install -y \
    build-essential \
    google-chrome-stable \
    libpoppler-cpp-dev \
    pkg-config \
    unzip \
    && curl -o /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/${CHROME_VERSION}/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && sudo -u airflow pip install -r /home/airflow/requirements.txt \
    && apt-get remove -y --autoremove \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /tmp/chromedriver.zip

# Set display port as an environment variable
ENV DISPLAY=:99

USER airflow
