FROM python:3.6.9-buster
LABEL maintainer="adrian.w.roque@gmail.com"

WORKDIR /usr/src/app

ARG CHROMIUM_VERSION=83.0.4103.116-1~deb10u3
ARG CHROMEDRIVER_VERSION=83.0.4103.39
RUN apt-get update && apt-get install -y chromium=$CHROMIUM_VERSION
RUN curl -LO https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip -d /usr/lib/chromium-browser						&& \
    ln -s /usr/lib/chromium-browser/chromedriver /usr/local/bin

RUN pip install centaurminer
RUN pip install pandas
RUN pip install redis
RUN pip install google-cloud-bigquery
RUN pip install pyarrow

COPY . .

ENV PROJECT_ID "for-adrian"
ENV TABLE_ID "urls.articles_redis"
ENV REDIS_SERVICE_HOST "redis-server"
ENV GOOGLE_APPLICATION_CREDENTIALS "credentials.json"

ENTRYPOINT ["python", "main.py"]
