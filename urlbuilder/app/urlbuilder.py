#!/usr/bin/python3

from urllib import parse
import centaurminer as mining
import pandas as pd
import datetime
import math
import time
import json
import uuid


"""URL Builder

The URL Builder is a utility built around Centaur Miner scraping mechanism. It aims to gather article URLs from a specific website and to send all this data to Google BigQuery. The BigQuery table is intended to have a similar appearance as the following table:

| url                | is_pdf |  status   | worker_id | timestamp  | ... |
|--------------------|--------|-----------|-----------|------------|-----|
| my.article.com/123 | 0      | Not Mined | *null*    | 2020-08-17 |     |
| my.article.com/456 | 0      | Working   | 001       | 2020-08-17 |     |
| my.article.com/789 | 1      | Done      | 001       | 2020-08-17 |     |

This is expected as the `URLBuilder` will work associated with the `JobDispatcher`, a special algorithm to organize and distribute the mining task amongst a single or several workers.
"""

class ScieloSearchLocations(mining.PageLocations):
    """HTML locations on the earch page to be gathered by centaurminer"""

    link_elem = mining.Element('css_selector', 'a.showTooltip').get_attribute('href')
    finish = mining.Element("css_selector", "div.midGlyph.alert")
    total_hits = mining.Element("css_selector", "#TotalHits")
    pass


class URLBuilder():
    """ Get URLs from Database and send to Google BigQuery"""
    
    def __init__(self, miner):
        """ URLBuilder constructor
        Args:
            miner (:obj: `centaurminer.Mining`): Mining Engine
            based on centaurMiner project.
        """
        self.miner = miner
        pass

    def _create_url_dataframe(self, source_page, **kwargs):
      """Prepare and parse URL data before results yield

      Args:
          source_page (string): The webpage where the links were retrieved from.
          **kwargs: Key-value pairs to be used as metadata information for the record
      Returns:
          pandas.DataFrame object with schema related information
      """
      self.miner.wd.get(source_page)
      links = self.miner.get(self.miner.site.link_elem, several=True)

      # Helper anonymous functions
      lang = lambda x: pd.Series({'language': dict(parse.parse_qsl(parse.urlsplit(x).query))['tlng']})  # Get article language from URL
      is_pdf = lambda x: pd.Series({'is_pdf': 1 if x.find('sci_pdf') != -1 else 0})                     # Get is_pdf information from URL
      # Remove unwanted links
      urls = [i for i in links if i.find('sci_arttext') != -1 or i.find('sci_pdf') != -1]

      df = pd.DataFrame()
      df['article_url'] = urls
      df['catalog_url'] = source_page
      df['is_pdf'] = df['article_url'].apply(is_pdf)
      df['language'] = df['article_url'].apply(lang)
      df['status'] = 'Not Mined'
      df['timestamp'] = pd.Timestamp(datetime.datetime.utcnow())
      df['worker_id'] = str(uuid.uuid1())
      df['meta_info'] = json.dumps(kwargs)
      return df


    def insert_into_gbq(self, search_url, delay_time=1):
        """Collect URLs until there's no more to send to GBQ.

        Args:
            search_url (string): Search page URL of search mechanism.
            delay_time (int, optional): Number of seconds of delay between
                search page requests.
        Returns:
            Number of URLs collected and sent to GBQ.
        """
        new_urls = self._create_url_dataframe(search_url)
        job = self.credentials.load_table_from_dataframe(
                new_urls, self.table_id, job_config=self.schema
                )
        job.result()
        time.sleep(delay_time)
        return len(new_urls)


    @classmethod
    def connect_to_gbq(cls, credentials, project_id, url_table_id, schema=None):
        """ Establish a connection with Google BigQuery
        Args:
            credentials (:obj: `google.auth.credentials.Credentials`):
                Google Authentication credentials object, required to
                authorize the data workflow between this class and the
                database. Can be declared from service or user account.
            project_id (string): Google Cloud project ID.
            table_id (string): Table information to read and write data on.
                Must be specified as `<dataset_name>.<table_name>`.
            schema (`list` of `dict`: optional): Optional databse schema to
                input while working with `pandas_gbq` module. If `None`, the
                schema will be inferred from `pandas.DataFrame` object.
        Example:
            URLBuilder.connect_to_gbq(google-credentials, 'MyProject',
              'my_dataset.my_table', [{'name': 'url', 'type': 'STRING'}]).
        Auth_docs:
            Reference for Google BigQuery Authentication, on this context:
            'https://pandas-gbq.readthedocs.io/en/latest/howto/authentication.html'
        """
        cls.credentials = credentials
        cls.project_id = project_id
        cls.table_id = url_table_id
        cls.schema = schema
        pass
