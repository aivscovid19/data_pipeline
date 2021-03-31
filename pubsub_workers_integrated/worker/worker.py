#!/usr/bin/env python

import json
import tldextract
from datetime import datetime, timezone
from google.cloud import pubsub_v1
from tables import StatusTable, DataTable
from site_worker_integrated import SiteWorkerIntegrated, MinerNotFoundError
from selenium.common.exceptions import WebDriverException
from google.cloud import logging
from os import environ

logging_client = logging.Client()
worker_name = environ.get("MINER_ID")
logger = logging_client.logger("workers")

statusTable = StatusTable().GetOrCreate()
dataTable = DataTable().GetOrCreate()

def LogToGCP(text):
    '''
    Log a message using google cloud logging, with the VM name at the beginning.
    '''
    global logger, worker_name
    logger.log_text(worker_name + ": " + text)


def callback(message):
    LogToGCP(f"\n [x] Received {message.data.decode('utf-8')}")
    LogToGCP("Delivery attempt number: " + str(message.delivery_attempt))
    status = json.loads(message.data.decode("utf-8"))

    # Tell bq that we received the request
    status['status'] = 'Started Mining'
    status['timestamp'] = datetime.utcnow()
    #status['timestamp'] = datetime.now(timezone.utc).isoformat()
    status['worker_id'] = worker_name
    errors = statusTable.insert_row(status)
    if errors != []:
        LogToGCP(f"We've got some errors when updating bq: {errors}")
        message.nack()
        return

    # Do the actual mining
    LogToGCP("Getting article info from " + status['article_url'])
    try:
        data = SiteWorkerIntegrated().send_request(status['article_url'])
    except MinerNotFoundError as e:
        LogToGCP("Mining failed: " + str(e))
        status['status'] = 'Failed - No miner'
        status['timestamp'] = datetime.utcnow()
        #status['timestamp'] = datetime.now(timezone.utc).isoformat()
        errors = statusTable.insert_row(status)
        message.nack()
        if errors != []:
            LogToGCP(f"We've got some errors when updating bq: {errors}")
        return
    except WebDriverException as e:  # Handle webdriver timeouts
        LogToGCP(str(e))
        status['status'] = 'Failed - Timeout'
        status['timestamp'] = datetime.utcnow()
        #status['timestamp'] = datetime.now(timezone.utc).isoformat()
        errors = statusTable.insert_row(status)
        message.nack()
        if errors != []:
            LogToGCP(f"We've got some errors when updating bq: {errors}")
        return
        
        
    if data is None:
        LogToGCP("Mining returned no results.")
        status['status'] = "Failed - No results"
        status['timestamp'] = datetime.utcnow()
        #status['timestamp'] = datetime.now(timezone.utc).isoformat()
        errors = statusTable.insert_row(status)
        if errors != []:
            LogToGCP(f"We've got some errors when updating bq: {errors}")
            message.nack()
            return
        message.ack()
        return
    if not data.get('language'):
        data['language'] = status['language']  # Should always be true...

    # Send results to the data table
    errors = dataTable.insert_row(data)
    if errors != []:
        LogToGCP(f"We've got some errors when updating bq: {errors}")

    # Send an update to bq that we're done
    status['status'] = 'Finished Mining'
    status['timestamp'] = datetime.utcnow()
    #status['timestamp'] = datetime.now(timezone.utc).isoformat()
    errors = statusTable.insert_row(status)
    if errors != []:
        LogToGCP(f"We've got some errors when updating bq: {errors}")
        message.nack()
        return

    LogToGCP(" [x] Done")
    LogToGCP(' [*] Waiting for messages.')
    message.ack()


if __name__ == "__main__":
    import uuid

    # extract environment variables
    project_id = DataTable.table_id.split('.')[0]
    subcription_ID = environ.get('PUBSUB_VERIFICATION_TOKEN')

    assert project_id is not None, "Include a .env file using the docker argument --env-file when running."

    LogToGCP(f"Miner started at {datetime.now().strftime('%d/%m/%y: %H:%M:%S')}.")
    LogToGCP(' [*] Waiting for messages.')

    # Create a subscriber
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subcription_ID)

    flow_control = pubsub_v1.types.FlowControl(max_messages=1)

    # Subscribe
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=callback,
        flow_control=flow_control
    )
    LogToGCP(f"Listening for messages on {subscription_path}")
    print(f"Listening for messages on {subscription_path}. Go to google logging to see status.")

    # Stop the thread from quitting until the job is finished
    try:
        streaming_pull_future.result()
    except Exception as e:
        LogToGCP(str(e))
        streaming_pull_future.cancel()
