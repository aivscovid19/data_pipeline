from datetime import datetime
import pandas as pd
from pandas.io import gbq

class JobDispatcher():
  '''
  JobDispatcher class retrieves urls_dataframe from a given BigQuery table,
  updates `status` of a job and returns urls_dataframefor further processing.

  Attributes:
    credentials (str): Credentials, either from user_account or service_account,
                        to authenticate to Google Cloud APIs.
    project_id (str): A project_id on Google Cloud Platform.
    url_table (str): A url_table to use to retrieve urls_dataframe from,
                      in form of `dataset_id.table_id`.
  '''

  def __init__(self, credentials, project_id, url_table):
    self.credentials = credentials
    self.project_id = project_id
    self.url_table = url_table
    
    # 'timestamp' field should be ```type:'DATETIME'```, bacause all ```url_builders``` use 'DATETIME' except Scielo.
    # Since we are mining Scielo, this field has been changed to ```type:'TIMESTAMP'```
    self.url_schema = [
        {'name': 'article_url', 'type': 'STRING',   'mode': 'REQUIRED'},
        {'name': 'catalog_url', 'type': 'STRING',   'mode': 'REQUIRED'},
        {'name': 'is_pdf',      'type': 'INTEGER',  'mode': 'REQUIRED'},
        {'name': 'language',    'type': 'STRING',                     },
        {'name': 'status',      'type': 'STRING',   'mode': 'REQUIRED'},
        {'name': 'timestamp',   'type': 'TIMESTAMP','mode': 'REQUIRED'},
        {'name': 'worker_id',   'type': 'STRING',                     },
        {'name': 'meta_info',   'type': 'STRING',                     },
    ]

  def register_job(self, worker_id, limit=100):
    ''' Retrieves urls_dataframe from a given BigQuery table,
    updates `worker_id`, and `status` of a job to `working on`,
    and uploades updated dataframe to a given BigQuery table. 

    Attributes:
      worker_id (str): A worker id responsible for this job.
      limit (str): A limit of urls to retrieve from the given BigQuery table.
                     Default is 100.

    Returns:
      urls_df(pandas dataframe): urls dataframe
    '''

    query = f"""
      SELECT article_url, catalog_url, is_pdf, language, meta_info 
      FROM (SELECT *, ROW_NUMBER() OVER
            (PARTITION BY article_url
            ORDER BY timestamp DESC) AS rank
            FROM {self.url_table})
      WHERE rank = 1 AND lower(status) = "not mined" AND is_pdf = 0
      ORDER BY timestamp
      LIMIT {limit}
    """
    urls_df = pd.read_gbq(query=query, project_id=self.project_id,
                      credentials=self.credentials)
    
    # Update status on URLBuilder table and upload it to BQ
    urls_df['status'] = 'working on'
    urls_df['timestamp'] = datetime.utcnow()
    urls_df['worker_id'] = worker_id
    urls_df.to_gbq(destination_table=self.url_table,
              project_id=self.project_id,
              if_exists='append',
              table_schema=self.url_schema,
              credentials=self.credentials)
    return urls_df
  
  def update_job_status(self, urls_df):
    ''' Updates `status' of the job to `done`
    and uploades updated dataframe to a given BigQuery table.

    Attributes:
      urls_df (pandas dataframe): A urls dataframe that was retrieved using
      `register_job` method. 
    '''

    urls_df['status'] = 'done'
    urls_df['timestamp'] = datetime.utcnow()
    urls_df.to_gbq(destination_table=self.url_table,
              project_id=self.project_id,
              if_exists='append',
              table_schema=self.url_schema,
              credentials=self.credentials)
    print("Done")
