# Load business logic
PROJECT_ID=$(gcloud config list --format 'value(core.project)' 2>/dev/null)
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} | grep "projectNumber" | sed 's|[^0-9]*||g')

if [ -z $PROJECT_ID ]; then
	echo "Failure in extracting GCP project id, insert it here: "
	read PROJECT_ID
fi

APPS=("sender" "worker")

# Load Environment Variables
if [ -f .env ]
then
  export $(cat .env | sed 's/#.*//g' | xargs)
fi

# Load sample table for integration tests

bq load --autodetect $STATUS_TABLE_ID scielo.csv

# Setup of PubSub topics
gcloud pubsub topics create $DEAD_LETTER_TOPIC_ID
gcloud pubsub subscriptions create dead-letter-$SUBSCRIBER_ID   \
     --topic=$DEAD_LETTER_TOPIC_ID                              \
     --ack-deadline=60                                          \
     --expiration-period=never

gcloud pubsub topics create $TOPIC_ID
gcloud pubsub subscriptions create $SUBSCRIBER_ID   \
     --topic=$TOPIC_ID                              \
     --dead-letter-topic=$DEAD_LETTER_TOPIC_ID      \
     --dead-letter-topic-project=$PROJECT_ID        \
     --ack-deadline=60                              \
     --expiration-period=never

PUBSUB_SERVICE_ACCOUNT="service-$PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com"

gcloud pubsub topics add-iam-policy-binding $DEAD_LETTER_TOPIC_ID \
    --member="serviceAccount:$PUBSUB_SERVICE_ACCOUNT"\
    --role="roles/pubsub.publisher"

gcloud pubsub subscriptions add-iam-policy-binding $SUBSCRIBER_ID \
    --member="serviceAccount:$PUBSUB_SERVICE_ACCOUNT"\
    --role="roles/pubsub.subscriber"

# Create, tag and push Docker images
for i in ${APPS[*]}; do
    docker build -t pubsub_${i} -f ${i}/Dockerfile .
    docker tag pubsub_${i} gcr.io/$PROJECT_ID/pubsub_${i}:latest
    docker push gcr.io/$PROJECT_ID/pubsub_${i}:latest
done

# Set up Kubernetes Engine
gcloud config set project $PROJECT_ID
gcloud config set compute/zone $ZONE
gcloud container clusters create $CLUSTER_NAME --num-nodes=3 --scopes=gke-default,pubsub,bigquery
gcloud container clusters get-credentials $CLUSTER_NAME

sed -i "s|PROJECT_ID|${PROJECT_ID}|g;s|TOPIC_ID|${TOPIC_ID}|g;s|SUBSCRIBER_ID|${SUBSCRIBER_ID}|g;s|STATUS_TABLE_NAME|${STATUS_TABLE_ID}|g" manifests/pubsub-sender-config.yaml
sed -i "s|PROJECT_ID|${PROJECT_ID}|g;s|TOPIC_ID|${TOPIC_ID}|g;s|SUBSCRIBER_ID|${SUBSCRIBER_ID}|g;s|STATUS_TABLE_NAME|${STATUS_TABLE_ID}|g;s|DATA_TABLE_NAME|${DATA_TABLE_ID}|g" manifests/pubsub-worker-config.yaml
for i in ${APPS[*]}; do
    sed -i "s|PROJECT_ID|${PROJECT_ID}|g" manifests/pubsub-${i}.yaml
    kubectl apply -f ./manifests/pubsub-${i}-config.yaml
    kubectl apply -f ./manifests/pubsub-${i}.yaml
done
