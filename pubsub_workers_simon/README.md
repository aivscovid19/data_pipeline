# Pipeline for URL distribution

## Overview
We use the Google Pub/Sub API to handle job distribution, where each worker (subscriber) is given one URL to work on independently. When it finishes, Pub/Sub will send the subscriber another URL to mine. Both the sender (Publisher) and receiver (subscriber) sides of Pub/Sub need to run constantly, so each one has its own docker container to set up.

## Setup
We are going to assume you're working in a [google cloud project (GCP)](https://cloud.google.com/), but you can follow similar steps at every point to set this up for a standalone linux server or any other organization of servers. You'll need to handle the google credentials however you do it - we'll need access to the bigquery and Pub/Sub APIs. Using GCP, go to the bigquery page and click **Enable API**, and likewise for Pub/Sub.

### Creating VMs
Because everything is packaged into docker containers, you should use VMs with the [Container-Optimized OS](https://cloud.google.com/container-optimized-os/docs) (COS), for security and to limit startup times and VM size. If you want to use a regular OS (debian/ubuntu/linux/etc) you'll need to install docker yourself. There are no other prerequisites, thanks to the containerization. To use the COS, click "Change" in the **Boot Disk** section, and select "Container Optimized OS" in the "Operating System" dropdown.

When setting up a VM, make sure to change the **Access Scopes** to either "Allow full access to all Cloud APIs", or "Set Access for each API" and set the **BigQuery** and **Pub/Sub** dropdowns to "Enabled".

Copy this repo into your VM using:

```shell
git clone -b simon https://github.com/aivscovid19/data_pipeline.git
```

## Starting the Containers
Each of these containers will run endlessly, so they should continue until you use the `docker stop` command to stop them. If this doesn't happen, check the Troubleshooting section below.

### 1) Consumer containers
If you want to run a subscriber on this machine, simply perform the following commands:

```shell
docker build -t pubsub_worker -f worker/Dockerfile .
docker run --rm -d --env-file .env pubsub_worker
```

### 3) Producer containers
If you want to run a publisher on this machine, you now need to set it up and create the container:

```shell
docker build -t pubsub_sender -f sender/Dockerfile .
docker run --rm -d --env-file .env pubsub_sender
```

## Adding Miners
When you eventually add miners to this container network, you'll do so by adding your miner python file to worker/miners/. Then update worker/miners/__init__.py to import your module, and look at the example (worker/miners/arxiv.py) to see what functions you need and how to set them up. Namely, you need the `GetArticle(url)` function, which returns a dictionary of the data in the article. I recommend you use centaurminer to collect the data, since it keeps the scraping process pretty simple. But remember if you do, that you may need to do some reworking of the data after it's mined (like is done in [arxiv.py](worker/miners/arxiv.py)) to mold the data from the article to align with the schema of the data table, and to get dates in a proper format.

## Troubleshooting
If your containers stop running shortly after you start them, you can rerun the `docker run` command, but exclude the `-d` flag. This will start the container without detaching, so you can see the logs and failure message.
