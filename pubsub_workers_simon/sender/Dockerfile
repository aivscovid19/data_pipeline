FROM python:3.8-buster

WORKDIR /usr/source/etc/pubsub/

#COPY sender/ .
#COPY tables/ tables/
#COPY requirements.txt ./
COPY sender/Pipfile .
COPY sender/Pipfile.lock .

RUN pip install pipenv \
 && pipenv install

COPY tables/ tables/
COPY sender/send.py .
COPY sender/templates/ templates/

#RUN pip install --no-cache-dir -r requirements.txt

#ENTRYPOINT ["pipenv", "run", "python", "send.py"]
#CMD exec pipenv run gunicorn --bind :8080 send:app
ENTRYPOINT ["pipenv", "run", "python", "send.py"]
#CMD pipenv run gunicorn --bind:8080  --workers 1 --worker-class uvicorn.workers.UvicornWorker  --threads 8 app.main:main.py
