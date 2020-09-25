#!/usr/bin/python3

from urllib import parse
import centaurminer as mining
import pandas as pd
import pandas_gbq
import datetime
import math
import time
import json
from builders import ScieloBuilder


"""# URL Builder

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


    def dataframe_generator(self, domain, keywords, limit=None):
        """ Collect article URLS and return them as a generator.
        Args:
            base_url (str):
                Default search page from website.
            keywords (`list` of `str`):
                List of keywords to search from domain.
            limit (int):
                Max number of pages to include in BigQuery.
        Returns:
            Generator of URLs collected during this process.
            Creates a list of 15 urls at each iteration.
        """

        count = 0

        # Gather search meta information: max number of results
        # and max number of pages
        self.miner.wd.get(self._search_url(domain, keywords))
        URLS_PER_PAGE = 15
        total_hits = int(self.miner.get(self.miner.site.total_hits).replace(' ', ''))
        n_pages = math.ceil(total_hits / URLS_PER_PAGE)

        # If there's no limit, fetch all article urls and data
        if limit is None:
            limit = total_hits
        for i in range(n_pages):
            source_page = self._search_url(domain, keywords, i + 1)
            self.miner.wd.get(source_page)
            
            # No more URLs available
            if self.miner.get(self.miner.site.finish):
                return

            # Get the links and send to dataframe
            # Additional parameters will be inserted into meta_info field
            links = self.miner.get(self.miner.site.link_elem, several=True)
            df = self._create_url_dataframe(links, source_page, search_terms=keywords)
            
            # Gather no more than `limit` urls
            count += len(df)
            if count < limit:
                yield df
            else:
                yield df.iloc[:limit - count] # Limit is reached, stop gathering data
                return


    def collect(self, base_url, keywords, limit=100, delay_time=1):
        """Collect URLs until there's no more to send to GBQ.

        Args:
            base_url (string): Domain URL for search mechanism.
            keywords (`list` of `int`): List of keywords to search for.
            limit (int, optional): Max number of URLs to collect to GBQ.
            delay_time (int, optional): Number of seconds of delay between
                search page requests.
        Returns:
            Number of URLs collected and sent to GBQ.
        """
        total = 0
        for new_urls in self.dataframe_generator(base_url, keywords, limit):
            pandas_gbq.to_gbq(new_urls, self.table_id, self.project_id,
                              if_exists='append', table_schema=self.schema)
            time.sleep(delay_time)
            n = len(new_urls)
            if n:
                print(f"Sending {n} URLs to {self.table_id} on Google Bigquery")
                total += n
        return total


    @staticmethod
    def _create_url_dataframe(links, source_page, **kwargs):
      """Prepare and parse URL data before results yield
      Args:
          links (`list` of `str`): article URLs from search webpage.
          source_page (string): The webpage where the links were retrieved from.
          **kwargs: Key-value pairs to be used as metadata information for the record
      Returns:
          pandas.DataFrame object with schema related information
      """

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
      df['timestamp'] = datetime.datetime.utcnow()
      df['worker_id'] = None
      df['meta_info'] = json.dumps(kwargs)
      return df


    @staticmethod
    def _search_url(domain, search_terms, page_index=1, urls_per_page=15):
        """Build page search URL from input search terms
        Args:
            domain(string): Web domain of the search webpage
            search_terms(`list` of `str`): List of search terms requested
            current_page (int, optional): Page index of the search results.
                Defaults to first page of search results.
            urls_per_page(int, optional): Max number of urls from search page.
                Defaults to standard number of results on this website.
        Returns:
            URL-like string which redirects to first search page
        """
        parsed_url = parse.urlparse(domain)
        new_query = {}
        new_query['q'] = ' OR '.join([f'({term})' for term in search_terms])
        new_query['lang'] = 'en'
        new_query['count'] = urls_per_page
        new_query['from'] = urls_per_page * (page_index - 1) + 1    # Index of first article URL shown
        new_query['output'] = 'site'
        new_query['sort'] = ''
        new_query['format'] = 'summary'
        new_query['fb'] = ''
        new_query['page'] = page_index
        new_query['filter[in][]'] = 'scl'     # Filter results only in Brazilian Scielo
        # Rebuild the URL with queries
        new_url = parse.urlunparse(parsed_url._replace(query = parse.urlencode(new_query)))
        return f"{new_url}&q={parse.quote_plus(new_query['q'])}&lang={new_query['lang']}&page={page_index}"


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
