FROM python:3.8-buster

WORKDIR /usr/source/etc/rabbitmq/

COPY worker/Pipfile .
COPY worker/Pipfile.lock .

# Install chrome first
RUN apt-get update \
 && curl https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb \
 && dpkg -i chrome.deb || apt-get install -yf \
 && rm chrome.deb

# Set up the packages needed
RUN pip install pipenv \
 && pipenv install

COPY worker/ .
COPY tables/ tables/

# python worker.py
#CMD ['python', 'worker.py']
ENTRYPOINT ["pipenv", "run", "python", "worker.py"]
#ENTRYPOINT ["tail", "-f", "/dev/null"]

