# URL Builder

Fetch and store article links from several scientific websites.

## Architecture

![URL Builder Kuberenetes cluster architecture](./images/urlbuilder.png)


To achieve scalability and distribuition of the system, I take an approach of distributing search pages from a website query to several worker running on a Kubernetes ReplicaSet. To make this work, a single Python application will take the query as a user input and build a list of URLs with search results to be sent to a Redis Pub/Sub queue. At any time, the URL builders can receive a job through this queue and start to work with it. If a URL Builder is currently working on a given search result page, the next one will be addressed to the next available replica. To make this work, the URL Builders will have to continuously listen to queue requests. To maintain a minimal number of builders working, we should use the GKE autoscaling function.

### Available Websites

- `scielo`
