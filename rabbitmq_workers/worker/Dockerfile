FROM python:3.8-buster

WORKDIR /usr/source/etc/rabbitmq/

# Install google chrome
RUN apt-get update \
 && curl https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb \
 && dpkg -i chrome.deb || apt-get install -yf \
 && rm chrome.deb

COPY worker/Pipfile .
COPY worker/Pipfile.lock .

# Set up the packages needed
RUN pip install pipenv \
 && pipenv install

# Copy custom data
COPY worker/ .
COPY tables/ tables/
COPY CENTAURminer/centaurminer/ centaurminer/

# python worker.py
#CMD ['python', 'worker.py']
ENTRYPOINT ["pipenv", "run", "python", "worker.py"]
#ENTRYPOINT ["tail", "-f", "/dev/null"]

