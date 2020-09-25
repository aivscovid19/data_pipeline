#!venv /usr/bin/python3

from google.oauth2.service_account import Credentials
from urlbuilder import URLBuilder
import centaurminer as mining
import pandas_gbq
import sys
import os
import builders

# The order is important here.
# Be careful before changing any value.
url_schema = [
    {'name': 'article_url', 'type': 'STRING',   'mode': 'REQUIRED'},
    {'name': 'catalog_url', 'type': 'STRING',   'mode': 'REQUIRED'},
    {'name': 'is_pdf',      'type': 'INTEGER',  'mode': 'REQUIRED'},
    {'name': 'language',    'type': 'STRING'                      },
    {'name': 'status',      'type': 'STRING',   'mode': 'REQUIRED'},
    {'name': 'timestamp',   'type': 'DATETIME', 'mode': 'REQUIRED'},
    {'name': 'worker_id',   'type': 'STRING'                      },
    {'name': 'meta_info',   'type': 'STRING'                      }
]



def main():

    # Google BigQuery Authentication. At first, we'll try to fetch
    # authentication data from a 'credentials.json' file at our 
    # working directory. If this file doesn't exist, we authenticate
    # with web login.
    try:
        cred_file = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        credentials = Credentials.from_service_account_file(cred_file)
    except (KeyError, FileNotFoundError):
        print("Invalid credentials. Set GOOGLE_APPLICATION_CREDENTIALS to your credentials file.");
        exit(1);

    # Project, dataset and table configuration
    pandas_gbq.context.credentials = credentials
    project_id   = os.environ["PROJECT_ID"]
    url_table_id = os.environ["TABLE_ID"]

    #driver_path='/usr/lib/chromium-browser/chromedriver'

    miner_name = sys.argv[1]
    #site_miner = getattr(builders, miner_name, None)
    site_builder = builders.get(miner_name)
    #assert site_miner is not None, f"Could not find the miner requested: {sys.argv[0]}"

    #miner = mining.MiningEngine(ScieloSearchLocations, driver_path=driver_path)
    site_builder.connect_to_gbq(credentials, project_id, url_table_id, url_schema)
    #URLBuilder.connect_to_gbq(credentials, project_id, url_table_id, url_schema)

    #scielo_builder = URLBuilder(miner)

    # Collect these number of URLs and store them in pd.DataFrame
    #search_domain = 'https://search.scielo.org/'
    search_terms = sys.argv[2:-1]
    limit = int(sys.argv[-1])
    site_builder.collect(search_terms, limit)
    print("Finished with collection", flush=True)
    #site_builder.collect(search_domain, search_terms, limit)
    #scielo_builder.collect(search_domain, search_terms, limit)


if __name__  == "__main__":
    main()
