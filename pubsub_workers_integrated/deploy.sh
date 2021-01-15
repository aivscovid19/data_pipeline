# Load business logic
PROJECT_ID=$(gcloud config list --format 'value(core.project)' 2>/dev/null)
APPS=("sender" "worker")

# Load Environment Variables
if [ -f .env ]
then
  export $(cat .env | sed 's/#.*//g' | xargs)
fi

# Setup of PubSub topics
gcloud pubsub topics create $TOPIC_ID
gcloud pubsub topics create $DEAD_LETTER_TOPIC_ID
gcloud pubsub subscriptions create $SUBSCRIBER_ID   \
     --topic=$TOPIC_ID                              \
     --dead-letter-topic=$DEAD_LETTER_TOPIC_ID      \
     --dead-letter-topic-project=$PROJECT_ID        \
     --ack-deadline=60                              \
     --expiration-period=never

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
