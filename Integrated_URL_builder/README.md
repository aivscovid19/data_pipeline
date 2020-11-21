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

Create an instance to run it on:

Go to the VM instances page in your project and click on “Create Instance”. In here, make sure to change the following settings:

- Change the name to something recognizable
- Change the boot disk to “Container Optimized OS”
- Change “Access Scopes” to either allow Bigquery specifically, or just “Allow full access”
- Check the “Allow HTTP” and “Allow HTTPS” checkboxes

Click “Create”.


## Working:

This container was tested only in Google Compute Engine VMs, so this should be a good starting point to run this application. This is a good piece of advice, as we don't recommend doing web scraping on your local machine. To get things working easily, create this VM with a Service Account with read and write permissions to BigQuery.


To start working on it, first clone the repository to your machine:

```shell
$ git clone https://github.com/aivscovid19/data_pipeline.git
```

Change to the Integrated_URL_builder folder:

```shell
$ cd data_pipeline/Integrated_URL_builder
```


To get the google credentials file:

- Go the this [link]{https://console.cloud.google.com/apis/credentials/serviceaccountkey?_ga=2.258827587.814981471.1605932487-1580510446.1593694724}
- From the Service account list, select New service account.
- In the Service account name field, enter a name.
- From the Role list, select BigQuery > BigQuery Admin.
- Click Create. A JSON file that contains your key downloads to your computer.

#### Store the google credentials file in the Integrated_URL_builder folder. 

Then, build the docker using the following command:

```shell
$ docker build -t url_builder .
```

Run the docker using your desired inputs:

```shell
$ docker run -d --rm --name URL_Builder 			\ 
    --env DOMAIN='arxiv'                            		\    
    --env PROJECT_ID='for-yr'                        		\    
    --env TABLE_ID='Medical_Dataset.arxiv_urls'      		\    
    --env SEARCH_WORD='coronavirus'                 		\    
    --env LIMIT=100                                   		\    
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

