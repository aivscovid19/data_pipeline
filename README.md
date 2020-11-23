# data_pipeline
collect and process data

An overview of the workflow is shown in [workflow_diagram](workflow_diagram/).

The current status of the URLBuilder section is contained in [updated_urlbuilder](updated_urlbuilder), and the status of the site worker/miner section is contained in [pubsub_workers](pubsub_workers) or [rabbitmq_workers](rabbitmq_workers).

Note that rabbitmq workers are currently more stable regarding the queueing system (because it's simpler), but pubsub has additional work from Gulnoza, in implementing a factory method for choosing a worker.

# Motivation

# Architecture Overview

## Google Cloud Platform Setup

The first steps comprises the Google Cloud Platform configuration and proper setup of the project and IAM service account and roles. If you don't have a project or a service account with the right permissions, you can create them with the following instructions:

    $ gcloud projects create <PROJECT_ID>
    $ gcloud iam service-accounts create <SERVICE_ACCOUNT_ID>
    $ gcloud projects add-iam-policy-binding <PROJECT_ID>					\
        --member="serviceAccount:<SERVICE_ACCOUNT_ID>@<PROJECT_ID>.iam.gserviceaccount.com"	\
        --role="roles/bigquery.dataOwner"

These commands will create a new GCP project, create a service account to connect to your Google Bigquery dataset and define IAM roles to give access to read and write data on the Google Bigquery. It's advised to run this program with service accounts, but it's possible to use your own Google Cloud IAM credentials.

# The URL Collector

## Installation

All you need to have to run these applications is the Docker environment set up and ready to container deployment. In this example, I'm assuming that the user has privileges on the `docker` group. If doesn't, the best workaround is to check the [Docker docs](https://docs.docker.com/engine/install/linux-postinstall/) regarding this topic or to execute all the following commands as super user (`sudo`).

This setup uses `redis` as the caching database / message broker. Therefore, it's suggested to pull the Redis image from the DockerHub with

    $ docker pull redis

If you're going to do the Google Kubernetes Engine approach, make sure that you have installed the `gcloud` and `kubectl` command line utilities, and that you have an available GCP project to use along with it.

## Getting Started

### General Advice

1. This container was tested only in Google Compute Engine VMs, so this should be a good starting point to run this application. We don't recommend doing web scraping on your local machine. To get things working easily, create this VM with a Service Account with read and write permissions to Google BigQuery.

### Docker 

To get this system running on a pure docker environment, it's required to set up a new network which will connect all the containers with the caching database. First of all, let's create our own private network with a `bridge` driver. 

    $ docker network create -d bridge pcn

With our new private container network, we can start deploying the database, which will give access to the subscription system. We will name it as `redis-server`, and we'll use this as a DNS address to connect our other applications to this database. If you want to name it in other way, you'll have to update the environment variable `REDIS_SERVICE_HOST` on the subsequent container deployments.

    $ docker run -d --rm --network pcn --name redis-server redis

With the caching database set, we can build and execute our catalog collector application. 

    $ docker build -t collector catalog_collector
    $ docker run --rm --network pcn collector KEYWORDS [LIMIT]

The purpose of this container is to run a job batch process. We define several keywords as the container parameters, with an option to declare the limit of articles to retrieve or not. If the `LIMIT` is not defined, all the search pages will be gathered and dumped into the Redis queue.

After the execution, several search pages will be available to the URL Builders to dump article links at the Google BigQuery. In this case, we can run the following commands.

    $ docker build -t builder urlbuilder
    $ docker run --rm --network pcn                                 \
        --env PROJECT_ID='my-project'                               \
        --env TABLE_ID='my-dataset.my-table'                        \
        --env GOOGLE_APPLICATION_CREDENTIALS='my-credentials.json'  \
        builder

The credentials file must be setup accordingly on the urlbuilder directory, as `credentials.json`, and with read and write privileges to BigQuery.

### Google Kubernetes Engine

It's advised to get a basic grasp on how Kubernetes works before moving to a test with the Google Kubernetes Engine

Create a new Google Kubernetes Engine cluster. We're not going through the details on this tutorial. You can follow the instructions on [Creating a zonal cluster](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-a-zonal-cluster) before proceeding. We've been testing this setup with a pool of 3 nodes running `e2-medium` Compute Engine instances, but a lighter setup could probably run it as well.

After setting up a new GKE cluster, connect to it to be able to use the `kubectl` command line utility. You can use the following command to achieve this. 

    gcloud container clusters get-credentials <your-cluster-name> --zone <your-cluster-zone> --project <your-gcp-project>

Now let's change the configuration; open the file `manifests/config.yaml` and update the fiels `PROJECT_ID` and `TABLE_ID` to your own Google BigQuery configuration. Open up the `manifests/collector-job.yaml` file and change your search parameters into the field `containers: args`.

After setting up the connection, apply the YAML files present on the `manifests` directory, in the following order.

    kubectl apply -f manifests/config.yaml
    kubectl apply -f manifests/redis.yaml
    kubectl apply -f manifests/urlbuilder.yaml
    kubectl apply -f manifests/collector-job.yaml

### Available Websites

- `scielo`

## Website Workers
