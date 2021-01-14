#!/usr/bin/env python
import base64
import json
import logging
import os

from flask import current_app, Flask, render_template, request
from google.cloud import pubsub_v1

# Read environment variables from a .env file
#import dotenv
#load_dotenv()

app = Flask(__name__)

# Configure the following environment variables via app.yaml
# This is used in the push request handler to verify that the request came from
# pubsub and originated from a trusted source.
app.config['PUBSUB_VERIFICATION_TOKEN'] = \
    os.environ['PUBSUB_VERIFICATION_TOKEN']
app.config['PUBSUB_TOPIC'] = os.environ['PUBSUB_TOPIC']
app.config['PROJECT'] = os.environ['GOOGLE_CLOUD_PROJECT']


# Global list to storage messages received by this instance.
MESSAGES = []

# Initialize the publisher client once to avoid memory leak
# and reduce publish latency.
publisher = pubsub_v1.PublisherClient()


# [START gae_flex_pubsub_index]
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html', messages=MESSAGES)

    data = request.form.get('payload', default='Example payload').encode('utf-8')

    # publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(
        current_app.config['PROJECT'],
        current_app.config['PUBSUB_TOPIC'])

    print("Publishing", flush=True)
    publisher.publish(topic_path, data=data)
    print("Finished publishing", flush=True)

    return 'OK', 200
# [END gae_flex_pubsub_index]


# [START gae_flex_pubsub_push]
@app.route('/pubsub/push', methods=['POST'])
def pubsub_push():
    '''
    Currently, no use for this. But it could be used to push messages to a subscriber.
    '''
    if (request.args.get('token', '') !=
            current_app.config['PUBSUB_VERIFICATION_TOKEN']):
        return 'Invalid request', 400

    envelope = json.loads(request.data.decode('utf-8'))
    payload = base64.b64decode(envelope['message']['data'])

    MESSAGES.append(payload)

    # Returning any 2xx status indicates successful receipt of the message.
    return 'OK', 200
# [END gae_flex_pubsub_push]


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    #app.run(host='0.0.0.0', port=8080)  # , debug=True)
    #app.run(host='127.0.0.1', port=8080, debug=True)

    #import pika
    import sys
    import json
    import time
    from datetime import datetime
    from tables import StatusTable
    #import time
    #from datetime import datetime
    #from os import environ
    #from google.cloud import bigquery
    #from tables import StatusTable
    #
    ## extract environment variables
    #mq_user = environ.get('RABBIT_USERNAME')
    #mq_pass = environ.get('RABBIT_PASSWORD')
    #host_ip = environ.get('RABBIT_HOST_IP')
    #
    DELAY = int(os.getenv('DELAY', '60'))
    #
    #assert None not in [mq_user, mq_pass, host_ip], "Include a .env file using the docker argument --env-file when running."
    #
    #credentials = pika.PlainCredentials(mq_user, mq_pass)
    #
    #connection = pika.BlockingConnection(
    #    pika.ConnectionParameters(host=host_ip, credentials=credentials))
    #channel = connection.channel()
    #
    #channel.queue_declare(queue='task_queue', durable=True)
    #
    statusTable = StatusTable().GetOrCreate()
    #
    ## Start the listening loop
    try:
        while True:  # Use sigint to break the loop
            newData = statusTable.GetNewURLs()
    #
            for row in newData:
                # Remove extra data that doesn't need to be sent
                row.pop('timestamp')
                row.pop('status')
    #
                request = json.dumps(row)
    #
                # Send the data through to the rabbitMQ queue
                topic_path = publisher.topic_path(
                    os.environ['GOOGLE_CLOUD_PROJECT'],
                    os.environ['PUBSUB_TOPIC'])

                print("Publishing", flush=True)
                publisher.publish(topic_path, data=request.encode("utf-8"))
    #            channel.basic_publish(
    #                exchange='',
    #                routing_key='task_queue',
    #                body=request,
    #                properties=pika.BasicProperties(
    #                    delivery_mode=2,  # make message persistent
    #                ))
                print(f" [x] Sent {request}", flush=True)
    #
                # Update the input row with a new timestamp and status, and add a row to the bq table
                row['timestamp'] = datetime.utcnow()
                row['status'] = "Sent to queue"
                #errors = bq_client.insert_rows(
                errors = statusTable.insert_row(row)
                if errors != []:
                    print(f"We've got some errors when updating bq: {errors}", flush=True)
            print(f"Sent {len(newData)} rows to pubsub queue.", flush=True)
    #
            # Wait for the next loop
            time.sleep(DELAY)
    except KeyboardInterrupt as e:
        print("ctrl+c caught - exiting", flush=True)
    except Exception as e:
        raise e
    #connection.close()
