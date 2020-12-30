# Pipeline for URL distribution

## Overview
We use the Google Pub/Sub API to handle job distribution, where each worker (subscriber) is given one URL to work on independently. When it finishes, Pub/Sub will send the subscriber another URL to mine. Both the sender (Publisher) and receiver (subscriber) sides of Pub/Sub need to run constantly, so each one has its own docker container to set up.

## Setup
We are going to assume you're working in a [google cloud project (GCP)](https://cloud.google.com/), but you can follow similar steps at every point to set this up for a standalone linux server or any other organization of servers. You'll need to handle the google credentials however you do it - we'll need access to the bigquery and Pub/Sub APIs. Using GCP, go to the bigquery page and click **Enable API**, and likewise for Pub/Sub.

If you're using the GCP Cloud Shell (recommended way), you may autohrize the API accesses as they are required by the Google Cloud services.

Copy this repo into your VM or CLoud Shell instance with:

```shell
git clone -b feature/k8s https://github.com/aivscovid19/data_pipeline.git
cd data_pipeline/pubsub_workers_integrated
```

## Setup - Google Kubernetes Engine

The Kubernetes way to deploy the mining system folows the same fashion as the containers isolated, at least until some point. First of all, we need to build the Docker images as we did in an isolated environment.

```
cd pubsub_workers_integrated
docker build -t pubsub_sender -f sender/Dockerfile .
docker build -t pubsub_worker -f worker/Dockerfile .
```

To make things easier, let's create some environment variables with our project ID, a compute region and a cluster name of your choice. You can't select any value to your region, you need to choose one from the [available regions](https://cloud.google.com/compute/docs/regions-zones#available) of Google Cloud Platform.

```
export PROJECT_ID=$(gcloud config list --format 'value(core.project)' 2>/dev/null
export CLUSTER_NAME=<my-cluster-name>
export REGION=<my-region>
```

After building the images, it's required to tag and upload the images to the Google Container Registry. The whole process may be found at GCP documentation, but here's a summary with the main instructions. **Be careful:** You must set Google Storage permissions to upload images to the Container Registry. This can be set with Cloud API permissions on a Google Compute Engine instance. For more information regarding this issue, look for the [GCP reference documentation](https://cloud.google.com/container-registry/docs/pushing-and-pulling).

```
docker tag pubsub_sender gcr.io/$PROJECT_ID/pubsub_sender:latest
docker tag pubsub_worker gcr.io/$PROJECT_ID/pubsub_worker:latest
docker push gcr.io/$PROJECT_ID/pubsub_sender:latest
docker push gcr.io/$PROJECT_ID/pubsub_worker:latest
```

Let's move on to the GKE setup on itself. We are going to use the `gcloud` CLI utility tool, which can be installed on your local machine or a GCE instance, or directly from the GCP console Cloud Shell. First, we're going to set up a basic GCP configuration. Right after this, we create a new GKE cluster with 3 nodes and get its credentials; that way, we bind the cluster credentials to our `kubectl` CLI tool. **You may choose another name to export your own cluster name**.

```

gcloud config set project $PROJECT_ID
gcloud config set compute/zone $REGION
gcloud container clusters create $CLUSTER_NAME --num-nodes=3
gcloud container clusters get-credentials $CLUSTER_NAME
```

At this point, it's required to change the values of **environment variables** and the GCR container path on the YAML files. Finally, we are ready to deploy. At the beginning, we'll deploy the ConfigMaps. Right after it, we may apply the Deployments.

```
kubectl apply -f ./manifests/pubsub-sender-config.yaml
kubectl apply -f ./manifests/pubsub-worker-config.yaml
kubectl apply -f ./manifests/pubsub-sender.yaml
kubectl apply -f ./manifests/pubsub-worker.yaml
```

## Monitoring

To check if your Kubernetes pods are running as expected, you may use the command `kubectl get pods`.
