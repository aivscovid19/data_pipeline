FROM python:3.8-buster

WORKDIR /usr/source/etc/pubsub/

#COPY sender/ .
#COPY tables/ tables/
#COPY requirements.txt ./
COPY send.py .
COPY Pipfile* .

RUN pip install pipenv \
 && pipenv install

#RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["pipenv", "run", "python", "send.py"]
