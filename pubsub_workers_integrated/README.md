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
cd pubsub_worker_integrated
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

## Setup - Google Kubernetes Engine

The Kubernetes way to deploy the mining system folows the same fashion as the containers isolated, at least until some point. First of all, we need to build the Dokcer images as we did in an isolated environment.

```
cd pubsub_workers_integrated
docker build -t pubsub_sender -f sender/Dockerfile .
docker build -t pubsub_worker -f worker/Dockerfile .
```

After building the images, it's required to tag and upload the images to the Google Container Registry. The whole process may be found at GCP documentation, but here's a summary with the main instructions. **Be careful:** You must set Google Storage permissions to upload images to the Container Registry. This can be set with Cloud API permissions on a Google Compute Engine instance. For more information regarding this issue, look for the GCP docs.

```
docker tag pubsub_sender gcr.io/<PROJECT-ID>/pubsub_sender:latest
docker tag pubsub_worker gcr.io/<PROJECT-ID>/pubsub_worker:latest
docker push gcr.io/<PROJECT-ID>/pubsub_sender:latest
docker push gcr.io/<PROJECT-ID>/pubsub_worker:latest
```

Let's move on to the GKE setup on itself. We are going to use the `gcloud` CLI utility tool, which can be installed on your local machine or a GCE instance, or directly from the GCP console Cloud Shell. First, we're going to set up a basic GCP configuration. Right after this, we create a new GKE cluster with 3 nodes and get its credentials; that way, we bind the cluster credentials to our `kubectl` CLI tool.

```
gcloud config set project <PROJECT-ID>
gcloud config set compute/zone <COMPUTE-ZONE>
gcloud container clusters create <CLUSTER-NAME> --num-nodes=3
gcloud container clusters get-credentials <CLUSTER-NAME>
```

At this point, it's required to change the values of **environment variables** and the GCR container path on the YAML files. Finally, we are ready to deploy. At the beginning, we'll deploy the ConfigMaps. Right after it, we may apply the Deployments.

```
kubectl apply -f ./manifests/pubsub-sender-config-ym7i.yaml
kubectl apply -f ./manifests/pubsub-worker-config-gjp9.yaml
kubectl apply -f ./manifests/pubsub-sender.yaml
kubectl apply -f ./manifests/pubsub-worker.yaml
``` 

## Adding Miners
When you eventually add miners to this container network, you'll do so by adding your miner python file to worker/miners/. Then update worker/miners/__init__.py to import your module, and look at the example (worker/miners/arxiv.py) to see what functions you need and how to set them up. Namely, you need the `GetArticle(url)` function, which returns a dictionary of the data in the article. I recommend you use centaurminer to collect the data, since it keeps the scraping process pretty simple. But remember if you do, that you may need to do some reworking of the data after it's mined (like is done in [arxiv.py](worker/miners/arxiv.py)) to mold the data from the article to align with the schema of the data table, and to get dates in a proper format.

## Troubleshooting
If your containers stop running shortly after you start them, you can rerun the `docker run` command, but exclude the `-d` flag. This will start the container without detaching, so you can see the logs and failure message.
