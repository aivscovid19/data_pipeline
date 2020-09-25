#!/usr/bin/env python
import pika
import time
import json
from os import environ
from urllib.parse import urlparse
import uuid
from datetime import datetime
from google.cloud import bigquery
from tables import StatusTable, DataTable

self_id = str(uuid.uuid1())  # Use uuid1 so the network ID is in the uuid, and we can trace it back to this machine.

# extract environment variables
mq_user = environ.get('RABBIT_USERNAME')
mq_pass = environ.get('RABBIT_PASSWORD')
host_ip = environ.get('RABBIT_HOST_IP')
#project_id = environ.get('PROJECT_ID')

assert None not in [mq_user, mq_pass, host_ip], "Include a .env file using the docker argument --env-file when running."

credentials = pika.PlainCredentials('guest','guest')
#credentials = pika.PlainCredentials(mq_user, mq_pass)

connection = pika.BlockingConnection(
    #pika.ConnectionParameters(host='35.223.198.161', credentials=credentials))
    pika.ConnectionParameters(host=host_ip, credentials=credentials))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C', flush=True)

statusTable = StatusTable().GetOrCreate()
dataTable = DataTable().GetOrCreate()

#bq_client = bigquery.Client()
#table = bq_client.get_table('urls.status')

def callback(ch, method, properties, body):
    status = json.loads(body)
    print("\n [x] Received %r" % body, flush=True)

    # Tell bq that we received the request
    status['status'] = 'Started Mining'
    status['timestamp'] = datetime.utcnow()
    status['worker_id'] = self_id
    #bq_client.insert_rows(
    #        table = table,
    #        rows = [status]
    #)
    print("status:")
    print(status)
    errors = statusTable.insert_row(status)
    if errors != []:
        print(f"We've got some errors when updating bq: {errors}", flush=True)

    # Do the actual mining
    import miners
    print("getting article info from", status['article_url'], flush=True)
    #domain = status['catalog_url'].split(".")[0]
    domain = urlparse(status['article_url']).netloc.split('.')[1]  # Get rid of the extension and subdomain
    print("Using domain:", domain, flush=True)
    miner = getattr(miners, domain.lower(), None)
    if miner is None:
        print("Mining failed.", flush=True)
        status['status'] = 'Failed'
        status['timestamp'] = datetime.utcnow()
        errors = statusTable.insert_row(status)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        if errors != []:
            print(f"We've got some errors when updating bq: {errors}", flush=True)
        return
    data = miner.GetArticle(status['article_url'])
    if data is None:
        print("Mining returned no results.", flush=True)
        status['status'] = "No results"
        status['timestamp'] = datetime.utcnow()
        errors = statusTable.insert_row(status)
        if errors != []:
            print(f"We've got some errors when updating bq: {errors}", flush=True)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    data['language'] = status['language']  # Should always be true...
    print("\nGot data:", flush=True)
    print(*data.items(), sep='\n')

    # Send results to the data table
    errors = dataTable.insert_row(data)
    if errors != []:
        print(f"We've got some errors when updating bq: {errors}", flush=True)

    # Send an update to bq that we're done
    status['status'] = 'Finished Mining'
    status['timestamp'] = datetime.utcnow()
    errors = statusTable.insert_row(status)
    if errors != []:
        print(f"We've got some errors when updating bq: {errors}", flush=True)

    print(" [x] Done", flush=True)
    print(' [*] Waiting for messages. To exit press CTRL+C', flush=True)
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)

channel.start_consuming()
