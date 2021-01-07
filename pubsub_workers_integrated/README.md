# Pipeline for URL distribution

## Overview
We use the Google Pub/Sub API to handle job distribution, where each worker (subscriber) is given one URL to work on independently. When it finishes, Pub/Sub will send the subscriber another URL to mine. Both the sender (Publisher) and receiver (subscriber) sides of Pub/Sub need to run constantly, so each one has its own docker container to set up.

## Setup

We are going to assume you're working in a [google cloud project (GCP)](https://cloud.google.com/), but you can follow similar steps at every point to set this up for a standalone linux server or any other organization of servers. You'll need to handle the google credentials however you do it - we'll need access to the bigquery and Pub/Sub APIs. Using GCP, go to the [bigquery page](https://console.cloud.google.com/bigquery) and click **Enable API**, and likewise for [Pub/Sub](https://console.cloud.google.com/cloudpubsub).

If you're using the GCP Cloud Shell (recommended way), you may autohrize the API accesses as they are required by the Google Cloud services.

Copy this repo into your VM or Cloud Shell instance with:

```shell
git clone -b feature/k8s https://github.com/aivscovid19/data_pipeline.git
cd data_pipeline/pubsub_workers_integrated
```

# Quick Setup - Deploy Script

To make things easier, you may run the deployment script `deploy.sh` from a Cloud Shell or from your own shell with API access to the GCP. Before running it, you may need to edit the `.env` configuration file and overwrite the default values with the ones of your choice. This quick setup comprises all instructions present on the following sections, so feel free to use it as quick deploy tool.

```
vim .env      # Edit environment variables values
./deploy.sh
```

## Setup - Google Cloud Pub/Sub

We need to set up 2 topics and a subscriber before continuing. Every URL we want to mine is sent to Pub/Sub and stored in a topic, which is then sent to a subscriber. The subscriber will repeatedly try to mine the URL until it succeeds. We also need a second topic as a backup in case the mining repeatedly fails for some reason - if a miner fails to mine a URL more than 5 times (configurable), it's sent to a [dead letter topic](https://cloud.google.com/pubsub/docs/dead-letter-topics). Let's start by setting up environment variables, which you can change to fit your use (except for `PROJECT_ID`):

```
export PROJECT_ID=$(gcloud config list --format 'value(core.project)' 2>/dev/null)
export TOPIC_ID=<my-topic-name>
export DEAD_LETTER_TOPIC_ID=<my-dead-lettering-topic-name>
export SUBSCRIBER_ID=<my_subscriber_name>
```

Now use `gcloud` commands to create both topics, and then the subscriber that uses both of the topics:

```
gcloud pubsub topics create $TOPIC_ID
gcloud pubsub topics create $DEAD_LETTER_TOPIC_ID
gcloud pubsub subscriptions create $SUBSCRIBER_ID \
     --topic=$TOPIC_ID \
     --dead-letter-topic=$DEAD_LETTER_TOPIC_ID \
     --dead-letter-topic-project=$PROJECT_ID \
     --ack-deadline=60 \
     --expiration-period=never
```

## Setup - Google Bigquery

The way the code is set up, you don't need to manually set up bigquery before we start. However, you do have to decide a few table names. Every bigquery table is set up in a 3-tier naming scheme, like `project-id.dataset-id.table-id`. We will use 2 tables - the status table which acts as both an input for new URLs to mine and a log for current mining status for each URL, and the data table which is where the data from each article is sent. In the following commands, specify the dataset id and table name for each table, like `my-dataset.my-table`:

```
export STATUS_TABLE_ID=<my-dataset.my-table-name>
export DATA_TABLE_ID=<my-dataset.my-table-name>
```
(NOTE: The dataset and table names can only contain letters, numbers, and underscores.)
(NOTE: For now, the dataset must be created manually at this step - tables can still be created automatically. After merging, this is no longer required and this note can be removed.)

## Setup - Google Kubernetes Engine

The Kubernetes way to deploy the mining system folows the same fashion as the containers isolated, at least until some point. First of all, we need to build the Docker images as we did in an isolated environment.

```

docker build -t pubsub_sender -f sender/Dockerfile .
docker build -t pubsub_worker -f worker/Dockerfile .
docker image ls   # To check if the images were created succesfully. If not, run the build command again.
```

To make things easier, let's create some environment variables with our project ID, a compute zone and a cluster name of your choice. You can't select any value to your region, you need to choose one from the [available compute zones](https://cloud.google.com/compute/docs/regions-zones#available) of Google Cloud Platform.

```
export CLUSTER_NAME=<my-cluster-name>
export ZONE=<my-compute-zone>
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
gcloud config set compute/zone $ZONE
gcloud container clusters create $CLUSTER_NAME --num-nodes=3 --scopes=gke-default,pubsub,bigquery
gcloud container clusters get-credentials $CLUSTER_NAME
```

At this point, it's required to change the values of **environment variables** and the GCR container path on the YAML files. The following lines will make the changes according to the environment variables set up previously, using `sed`:

```
sed -i "s/PROJECT_ID/${PROJECT_ID}/g;s/TOPIC_ID/${TOPIC_ID}/g;s/SUBSCRIBER_ID/${SUBSCRIBER_ID}/g;s/STATUS_TABLE_NAME/${STATUS_TABLE_ID}/g" manifests/pubsub-sender-config.yaml
sed -i "s/PROJECT_ID/${PROJECT_ID}/g;s/TOPIC_ID/${TOPIC_ID}/g;s/SUBSCRIBER_ID/${SUBSCRIBER_ID}/g;s/STATUS_TABLE_NAME/${STATUS_TABLE_ID}/g;s/DATA_TABLE_NAME/${DATA_TABLE_ID}/g" manifests/pubsub-worker-config.yaml
sed -i "s/PROJECT_ID/${PROJECT_ID}/g" manifests/pubsub-sender.yaml
sed -i "s/PROJECT_ID/${PROJECT_ID}/g" manifests/pubsub-worker.yaml
```

Finally, we are ready to deploy. At the beginning, we'll deploy the ConfigMaps. Right after it, we may apply the Deployments.
```
kubectl apply -f ./manifests/pubsub-sender-config.yaml
kubectl apply -f ./manifests/pubsub-worker-config.yaml
kubectl apply -f ./manifests/pubsub-sender.yaml
kubectl apply -f ./manifests/pubsub-worker.yaml
```

## Monitoring

To check if your Kubernetes pods are running as expected, you may use the command `kubectl get pods`. If the Ready column has 1/1 for both rows, then it's working properly! If you see 0/1 and the status shows `ContainerCreating`, then you'll need to wait a few seconds and try again.

## Clean up

To avoid continuing charges, use the following steps to clean up the Pub/Sub, Bigquery, and Kubernetes resources. If you closed and re-opened the cloud shell after setting up the project, you'll need to re-run the lines above to store the environment variables.

```
gcloud pubsub subscriptions delete $SUBSCRIBER_ID
gcloud pubsub topics delete $TOPIC_ID
gcloud pubsub topics delete $DEAD_LETTER_TOPIC_ID

bq rm $STATUS_TABLE_ID
bq rm $DATA_TABLE_ID

gcloud container clusters delete -z $ZONE $CLUSTER_NAME
```

If you want to delete the whole bigquery dataset (instead of just the specific tables you're using here), run the following commands in addition:

```
bq rm -r ${STATUS_TABLE_ID%.*}
bq rm -r ${DATA_TABLE_ID%.*}
```
