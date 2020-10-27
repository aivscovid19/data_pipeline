#!/usr/bin/env python
import json
from urllib.parse import urlparse
from datetime import datetime
from google.cloud import pubsub_v1
from tables import StatusTable, DataTable


statusTable = StatusTable().GetOrCreate()
dataTable = DataTable().GetOrCreate()


def callback(message):
    status = json.loads(message.decode("utf-8"))
    print(f"\n [x] Received {message}", flush=True)

    # Tell bq that we received the request
    status['status'] = 'Started Mining'
    status['timestamp'] = datetime.utcnow()
    status['worker_id'] = self_id
    errors = statusTable.insert_row(status)
    if errors != []:
        print(f"We've got some errors when updating bq: {errors}", flush=True)

    # Do the actual mining
    import miners
    print("getting article info from", status['article_url'], flush=True)
    domain = urlparse(status['article_url']).netloc.split('.')[1]  # Get rid of the extension and subdomain
    print("Using domain:", domain, flush=True)
    miner = getattr(miners, domain.lower(), None)
    if miner is None:
        print("Mining failed.", flush=True)
        status['status'] = 'Failed'
        status['timestamp'] = datetime.utcnow()
        errors = statusTable.insert_row(status)
        message.ack()
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
        message.ack()
        return
    data['language'] = status['language']  # Should always be true...
    print("\nGot data:", flush=True)
    print(*data.items(), sep='\n', flush=True)

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
    message.ack()


if __name__ == "__main__":
    from os import environ
    import uuid

    self_id = str(uuid.uuid1())  # Use uuid1 so the network ID is in the uuid, and we can trace it back to this machine.

    # extract environment variables
    # project_id = environ.get('PROJECT_ID')
    project_id = StatusTable.table_id.split('.')[0]
    subcription_ID = environ.get('PUBSUB_VERIFICATION_TOKEN')

    assert project_id is not None, "Include a .env file using the docker argument --env-file when running."

    print(' [*] Waiting for messages. To exit press CTRL+C', flush=True)

    # Create a subscriber
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subcription_ID)

    # Subscribe
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=callback
    )
    print(f"Listening for messages on {subscription_path}", flush=True)

    # Stop the thread from quitting until the job is finished
    try:
        streaming_pull_future.result()
    except Exception:
        streaming_pull_future.cancel()
