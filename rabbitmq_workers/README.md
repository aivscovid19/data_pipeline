# Pipeline for URL distribution

## Overview
3 docker containers are needed to get the rabbitmq system to work:
* rabbitMQ service: Runs in the background, and it connects the producers and consumers through a managed queue
* producer: Repeatedly checks bigquery to see if any new URLs are available, and sends them to the queue if there are.
* consumer: Asks the queue for any available URLs, and mines the data at that URL whenever one comes in.

The main utility of RabbitMQ is to manage the collection and distribution of tasks, and to decouple the producers (from the URLbuilder process) from the consumers (the product of this portion of the project). By setting up a managed queue, we can remove problems arising from race conditions (if multiple workers are ready to mine data at once), and we can guarantee that all URLs are going to be mined. That is, if a worker crashes or otherwise fails to complete, rabbitMQ will send that URL/message to another worker to complete. This makes the distribution process robust and efficient.

## Setup

We are going to assume you're working in a [google cloud project (GCP)](https://cloud.google.com/), but you can follow similar steps at every point to set this up for a standalone linux server or any other organization of servers. You'll need to handle the google credentials however you do it - we'll need access to the bigquery API. Using GCP, go to the bigquery page and click **Enable API**.

### Firewall

In the GCP console, go to [VPC Network > Firewall](https://console.cloud.google.com/networking/firewalls/list). We need to set up 2 rules:
 * Anyone, anywhere can access port 8080 (rabbitMQ management port)
 * Any VM in our project can access ports 5671-5672 (message-sending ports)

1) Click **Create Firewall Rule**, and give the rule a descriptive name and description
2) Change the **Targets** dropdown to "All instances in the network".
3) Now select the "Specified Protocols and Ports" radio button in the **Protocols and Ports** section, and put ports "5671,5672" in the boxes for TCP and UDP
4) Put "10.128.0.0/24" in the **Source IP Range** (matches any VM in this project).
5) Click save, and the repeat steps 1-4 for the 8080 port, with the IP "0.0.0.0/0" as the **Source IP Range** (matches any IP).

Each of these 3 containers can be run on a single machine, or on separate machines. The only requirement is that the rabbitMQ service is created and running before any producers or consumers are created.

Additionally, between setting up the service and creating the producer/consumer containers, you need to create the credentials.env file. This contiains the rabbitMQ credentials (username and password) and the IP of the machine running the service.

### Creating VMs

Because everything is packaged into docker containers, you should use VMs with the [Container-Optimized OS](https://cloud.google.com/container-optimized-os/docs) (COS), for security and to limit startup times and VM size. If you want to use a regular OS (debian/ubuntu/linux/etc) you'll need to install docker yourself. There are no other prerequisites, thanks to the containerization. To use the COS, click "Change" in the **Boot Disk** section, and select "Container Optimized OS" in the "Operating System" dropdown.

When setting up a VM, make sure to change the **Access Scopes** to either "Allow full access to all Cloud APIs", or "Set Access for each API" and set the **BigQuery** dropdown to "Enabled".

## Starting the Containers

Each of these containers will run endlessly, so they should continue until you use the `docker stop` command to stop them. If this doesn't happen, check the Troubleshooting section below.

### 1) RabbitMQ background service

From this directory, run the following commands:

```shell
docker network create rabbit_network
docker run -d --rm --hostname rabbit_service --name rabbit_service -p 8080:15672 -p 5671:5671 -p 5672:5672 --network rabbit_network rabbitmq:3-management
```

Now you can use `docker ps` to see the service running, and you can direct your browser to "<this-vm-IP>:8080" to access the RabbitMQ management console. The default username/password is "guest"/"guest".

At this point, you have all of the information you need to set up your credentials/environment variables file. Do `cp example.env .env` and look at your newly created .env file. Follow the instructions to get the correct credentials and parameters in that file.

### 2) Consumer containers

If you want to run a worker on this machine, the next step is to set up the consumers that rabbitMQ sends messages to. Simply perform the following commands:

```shell
docker build -t rabbit_worker -f worker/Dockerfile .
docker run --rm -d --env-file .env rabbit_worker
```

For the second command above, make sure to include the `--network rabbit_network` flag if this is the same machine as the service you set up in step 1.

### 3) Producer containers

If you want to run a sender/listener on this machine, you now need to set it up and create the container:

```shell
docker build -t rabbit_sender -f sender/Dockerfile .
docker run --rm -d --env-file .env rabbit_sender
```

Once again, make sure to include the `--network rabbit_network` flag in the second command if this is the same machine as the service you set up in step 1.

## Adding Miners

When you eventually add miners to this container network, you'll do so by adding your miner python file to worker/miners/. Then update worker/miners/__init__.py to import your module, and look at the example (worker/miners/arxiv.py) to see what functions you need and how to set them up. Namely, you need the `GetArticle(url)` function, which returns a dictionary of the data in the article. I recommend you use centaurminer to collect the data, since it keeps the scraping process pretty simple. But remember if you do, that you may need to do some reworking of the data after it's mined (like is done in [arxiv.py](worker/miners/arxiv.py)) to mold the data from the article to align with the schema of the data table, and to get dates in a proper format.

## Troubleshooting

If your containers stop running shortly after you start them, you can rerun the `docker run` command, but exclude the `-d` flag. This will start the container without detaching, so you can see the logs and failure message. Here are the ones I've seen a lot, and how to fix them:

`"socket.gaierror: [Errno -2] Name or service not known"`: Make sure to include the "--network rabbit_network" flag if you're on the same machine as the rabbitMQ service.
`"pika.exceptions.AMQPConnectionError"`: Your .env file has the wrong IP address or hostname. Follow the instructions in the file to know what it should be.
