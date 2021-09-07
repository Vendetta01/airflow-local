FROM npodewitz/airflow-minimal:2.1.3-python3.8

ENV CHROME_VERSION=92.0.4515.107


USER root

# Installing chrome and chromedriver
RUN curl -q https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get -y update \
    && apt-get install -y google-chrome-stable unzip \
    && curl -o /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/${CHROME_VERSION}/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /tmp/chromedriver.zip

# Set display port as an environment variable
ENV DISPLAY=:99


USER airflow

COPY requirements.txt /home/airflow/requirements.txt
RUN pip install -r /home/airflow/requirements.txt
