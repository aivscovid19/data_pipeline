#!/usr/bin/env python
import pika
import sys
import json
import time
from datetime import datetime
from os import environ
from google.cloud import bigquery
from tables import StatusTable

# extract environment variables
mq_user = environ.get('RABBIT_USERNAME')
mq_pass = environ.get('RABBIT_PASSWORD')
host_ip = environ.get('RABBIT_HOST_IP')

DELAY = int(environ.get('DELAY'))

assert None not in [mq_user, mq_pass, host_ip], "Include a .env file using the docker argument --env-file when running."

credentials = pika.PlainCredentials(mq_user, mq_pass)
#credentials = pika.PlainCredentials('guest','guest')

connection = pika.BlockingConnection(
    #pika.ConnectionParameters(host='10.128.0.7', credentials=credentials))
    pika.ConnectionParameters(host=host_ip, credentials=credentials))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)

statusTable = StatusTable().GetOrCreate()

#def CollectURLsFromBQ(client = bigquery.Client()):
    #'''
    #Gather URLs from the globaly query named "QUERY".
#
    #The table you query from MUST have the schema discussed in our meetings.
    #'''
    #global QUERY
    #query_job = bq_client.query(QUERY)
    #rows = query_job.result()
    #json_rows = []
    #for row in rows:
        #row = dict(row)
        #row.pop('rn')  # Don't include the row number entry
        #json_rows.append(row)
    #return json_rows


#bq_client = bigquery.Client()
# Start the listening loop
try:
    while True:  # Use sigint to break the loop
        #newData = CollectURLsFromBQ()
        #newData = StatusTable.Query(QUERY)
        newData = statusTable.GetNewURLs()

        #table = bq_client.get_table('urls.status')
        for row in newData:
            # Remove extra data that doesn't need to be sent
            row.pop('timestamp')
            row.pop('status')

            request = json.dumps(row)

            # Send the data through to the rabbitMQ queue
            channel.basic_publish(
                exchange='',
                routing_key='task_queue',
                body=request,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ))
            print(f" [x] Sent {request}", flush=True)

            # Update the input row with a new timestamp and status, and add a row to the bq table
            row['timestamp'] = datetime.utcnow()
            row['status'] = "Sent to queue"
            #errors = bq_client.insert_rows(
            errors = statusTable.insert_row(row)
            if errors != []:
                print(f"We've got some errors when updating bq: {errors}", flush=True)
        print(f"Sent {len(newData)} rows to rabbitMQ queue.", flush=True)

        # Wait for the next loop
        time.sleep(DELAY)
except KeyboardInterrupt as e:
    print("ctrl+c caught - exiting", flush=True)
except Exception as e:
    raise e
connection.close()
