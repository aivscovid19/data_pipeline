# AIvsCOVID19  URL Builder

## Motivation
This repository contains a simple setup to create a URL Builder instance to act in the context of Data Mining workflow in the AIvsCOVID19 project. The URL Builder is a special type of data mining Python script; it iterates through search pages from a scientific article website, gathering all the links which could have valuable data to extract in a further process. At each iteration, the URL Builder will send the links extracted to a Google BigQuery table, given the right permissions to write data.

### Installation

Before proceeding, it's not advised to run this scraper on your local machine, as some websites may block yor IP address upon a number of requests on a particular domain. When data mining, be assured to follow very stricit ethical guidelines before running your process, to not clog up domain servers from scientific websites. **Be polite while mining data**.  

#### With Docker
The most common way to run this URL Builder script is to run it on a Docker container, as the dependencies will be updated to the latest working Python packages. To download the repository and build the Docker image, you can run the following command:

    git clone https://github.com/AdrianWR/urlbuilder.git
    docker build -t IMAGE_NAME urlbuilder

### Getting Started
At the moment of running the container, it's required to set up some environment variables at the runtime, related to the BigQuery authentication and authorization workflow. The followinf variables must be set:
- `PROJECT_ID`: Name of the Google Cloud project;
- `TABLE_ID`: In the format `dataset_id`.`table_id`. Required to declare the dataset to insert the information extracted from the search pages. Example: *urls.articles*;
- `GOOGLE_APPLICATION_CREDENTIALS`: Credentials file associated with the account with BigQuery permissions. On instructions with how to set up your credentials, follow [Service accounts](https://cloud.google.com/iam/docs/service-accounts). The following role permissions must be defined to the correct runtime of the URL Builder:


    - `bigquery.jobs.create`
    - `bigquery.tables.create`
    - `bigquery.tables.get`
    - `bigquery.tables.updateData`

To run the container on its own, it's possible to use the following command:
```
    docker run --rm -d
    --env PROJECT_ID="my-project"
    --env TABLE_ID="my-dataset.my-credentials"
    --env GOOGLE_APPLICATION_CREDENTIALS=/credentials.json
    --mount type=bind,source="$(pwd)"/credentials.json,target=/credentials.json,readonly
    IMAGE_NAME DOMAIN KEYWORDS LIMIT
```

The `KEYWORDS` argument could be one or more words, defining the search terms to genreate the links on the search mechanism. The `LIMIT` variable is an integer, representing how many links to gather and send to the BigQuery table.
