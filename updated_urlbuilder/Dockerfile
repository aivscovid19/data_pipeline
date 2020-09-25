FROM python:3.6.9-buster
LABEL maintainer="adrian.w.roque@gmail.com"

WORKDIR /usr/src/app

#ARG CHROMIUM_VERSION=83.0.4103.116-1~deb10u3
#ARG CHROMEDRIVER_VERSION=83.0.4103.39
#RUN apt-get update && apt-get install -y chromium=$CHROMIUM_VERSION
#RUN curl -LO https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
#    unzip chromedriver_linux64.zip -d /usr/lib/chromium-browser						&& \
#    ln -s /usr/lib/chromium-browser/chromedriver /usr/local/bin

 RUN apt-get update \
 && curl https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb \
 && dpkg -i chrome.deb || apt-get install -yf \
 && rm chrome.deb

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY urlbuilder urlbuilder

ENTRYPOINT ["python", "./urlbuilder"]
