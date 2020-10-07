FROM python:3.6.12-buster AS compiler
LABEL maintainer="adrian.w.roque@gmail.com"

WORKDIR /usr/src/app
ENV PATH=/root/.local/bin:$PATH

RUN apt-get update && \ 
    curl https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb && \
    dpkg -i chrome.deb || apt-get install -yf && \
    rm chrome.deb


COPY requirements.txt .
COPY credentials.json .
RUN pip install --user -r requirements.txt

COPY app .

ENV TABLE_ID "urlbuilder.links"
ENV REDIS_SERVICE_HOST "redis-server"

ENV GOOGLE_APPLICATION_CREDENTIALS "credentials.json"
ENTRYPOINT ["python", "."]