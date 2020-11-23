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


To get the google credentials file:

- Go to the service account page by clicking on this [link](https://console.cloud.google.com/apis/credentials/serviceaccountkey?_ga=2.258827587.814981471.1605932487-1580510446.1593694724).
- From the Service account list, select New service account.
- In the Service account name field, enter a name.
- From the Role list, select BigQuery > BigQuery Admin.
- Click Create.
- A JSON file that contains your key will start downloading to your computer, save the file as credentials.json. 
- Upload the credentials.json file into the VM instance.
- Move the file into the data_pipeline/Integrated_URL_builder folder.

After moving the file into the specified folder above, build the docker using the following command:

```shell
$ docker build -t url_builder .
```

Once the docker is built, run the docker to fetch URLs and save it in bigquery, but before running the code below, please ensure that the PROJECT_ID env variable is changed to the PROJECT_ID you are using. Change the other env variables as you wish; even if they are not changed, the docker will still run and save the results with the default env variable values in the code below.

```shell
$ docker run -d --rm --name URL_Builder \
  --env DOMAIN='arxiv'   \
  --env PROJECT_ID='for-yr'  \
  --env TABLE_ID='Medical_Dataset.arxiv_urls'   \
  --env SEARCH_WORD='coronavirus' \
  --env LIMIT=100  \
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


To check the logs while running the container:

```shell
$ docker logs URL_Builder
```

The docker shows the logs until the URLs are being scraped. Once the scraping is done, running this command will throw an error stating that there is no container running.
