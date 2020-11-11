# Integrated URL Builder

## Overview

URL builder to collect URLs and push to Bigquery from different journals:

[arXiv](http://export.arxiv.org/)

[bioRxiv](https://www.biorxiv.org/)

[medRxiv](https://www.medrxiv.org/)

[Preprints](https://www.preprints.org/)

[pbmc](http://pbmc.ibmc.msk.ru/)

[SciELO](https://search.scielo.org/)

The system is integrated with Docker.

## Installation:

All you need to run these applications is the Docker environment set up and ready for container deployment. In this example, I'm assuming that the user has privileges on the docker group. If it doesn't, the best workaround is to check the Docker docs regarding this topic or execute all the following commands as superuser (sudo).

This setup uses Redis as the caching database/message broker. Therefore, it's suggested to pull the Redis image from the DockerHub with

```shell
 $ docker pull redis
```

## Working:

This container was tested only in Google Compute Engine VMs, so this should be a good starting point to run this application. This is a good piece of advice, as we don't recommend doing web scraping on your local machine. To get things working easily, create this VM with a Service Account with read and write permissions to BigQuery.


To start working on it, first clone the repository to your machine:

```shell
$ git clone -b yeshwanth https://github.com/aivscovid19/data_pipeline.git
```



Then, build the docker using the following command:

```shell
$ docker build -t url_builder .
```

Run the docker using your desired inputs:

```shell
$ docker run -d --rm --name URL_Builder             \
    --env DOMAIN='arxiv'                            \    
    --env PROJECT_ID='for-yr'                        \    
    --env TABLE_ID='Medical_Dataset.arxiv_urls'      \    
    --env SEARCH_WORD='coronavirus'                  \    
    --env LIMIT=100                                   \    
	url_builder  
  ```

DOMAIN: journal from which the URLs need to be scraped.

Inputs: 
```shell
arxiv
biorxiv
medrxiv
preprint
pbmc
scielo
```

PROJECT_ID: Google cloud project_id.

TABLE_ID: Google cloud table_id to write the data into.

SEARCH_WORD: keyword to be searched.

LIMIT: number of URLs to be scraped.

The credentials file must be set up accordingly on the corresponding directory, as credentials.json, and with read and write privileges to BigQuery.

To check the logs while running the container:


```shell
$ docker logs URL_Builder
```

