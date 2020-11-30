# Integrated URL Builder

## Overview

URL builder to collect URLs and push to Bigquery from different journals:

[arXiv](http://export.arxiv.org/)

[bioRxiv](https://www.biorxiv.org/)

[medRxiv](https://www.medrxiv.org/)

[Preprints](https://www.preprints.org/)

[JAMA Network](https://jamanetwork.com/)

[pbmc](http://pbmc.ibmc.msk.ru/)

[SciELO](https://search.scielo.org/)

The system is integrated with Docker.

## Installation:

Create an instance to run it on:

Go to the VM instances page in your project and click on “Create Instance”. In here, make sure to change the following settings:

- Change the name to something recognizable
- Change the boot disk to “Container Optimized OS”
- Change “Access Scopes” to either allow Bigquery specifically, or just “Allow full access”

Click “Create.”


## Working:

To start working on it, first clone the repository to your machine:

```shell
$ git clone https://github.com/aivscovid19/data_pipeline.git
```

Change to the Integrated_URL_builder folder:

```shell
$ cd data_pipeline/Integrated_URL_builder
```

Build the docker by running the below command:

```shell
$ docker build -t url_builder .
```

If the docker is successfully built, the below statement will be printed:

```shell
Successfully tagged url_builder:latest
```

Once the docker is built, run the docker to fetch URLs and save it in bigquery, but before running the code below, please ensure that the PROJECT_ID env variable is changed to the PROJECT_ID you are using. Change the other env variables as you wish; even if they are not changed, the docker will still run and save the results with the default env variable values in the code below.

```shell
$ docker run -d --rm --name URL_Builder \
  --env DOMAIN='arxiv'   \
  --env PROJECT_ID='for-yr'  \
  --env TABLE_ID='Medical_Dataset.arxiv_urls'   \
  --env SEARCH_WORD='coronavirus' \
  --env LIMIT=100  \
  ---env TIME_FRAME=10\
  url_builder 
```

#### env variable inputs:

**DOMAIN**: journal from which the URLs need to be scraped.

Inputs: 
```shell
arxiv
biorxiv
medrxiv
preprint
jamanetwork
pbmc
scielo
```

**PROJECT_ID**: Input your google cloud project_id.

**TABLE_ID**: Input your google cloud DATASET and table_id to write the data into.

It'll be in the form: 'DATASET.table_id' Even if you didn't create a DATASET and a table in bigquery, they will automatically be created with the input names once               the above code snippet is ran.

**SEARCH_WORD**: Input the keyword to be searched.

**LIMIT**: Input the number of URLs to be scraped.

**TIME_FRAME**: Input the waiting time to send the each data_frame to bigquery.

## To check the logs while running the container:

```shell
$ docker logs -f URL_Builder
```

This command shows the continuous logs until the URLs are being scraped. 
