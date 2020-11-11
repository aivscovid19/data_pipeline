FROM python:3.6.12-buster AS compiler
LABEL maintainer="adrian.w.roque@gmail.com"

WORKDIR /usr/src/app
ENV PATH=/root/.local/bin:$PATH

ARG CHROMIUM_VERSION=83.0.4103.116-1~deb10u3
ARG CHROMEDRIVER_VERSION=83.0.4103.39
RUN apt-get update && apt-get install -y chromium=$CHROMIUM_VERSION
RUN curl -LO https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip -d /usr/lib/chromium-browser						&& \
    ln -s /usr/lib/chromium-browser/chromedriver /usr/local/bin

RUN curl https://raw.githubusercontent.com/AdrianWR/urlbuilder/master/urlbuilder/urlbuilder.py > urlbuilder.py

COPY credentials.json .


COPY url_builder_integration.py .

ENV DOMAIN "pbmc"
ENV PROJECT_ID "for-adrian"
ENV TABLE_ID "urlbuilder.pbmc"
ENV SEARCH_WORD "coronavirus"
ENV LIMIT "100"

ENV GOOGLE_APPLICATION_CREDENTIALS "credentials.json"

RUN pip install pandas_gbq
RUN pip install centaurminer

ENTRYPOINT ["python", "url_builder_integration.py"]
