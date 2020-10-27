import random, time
import pandas as pd
from pandas.io import gbq
from tld import get_fld
from job_dispatcher import JobDispatcher
from miners.ibmcru_miner import IbmcRuMiner
from miners.arxiv_miner import ArxivMiner
from miners.biorxiv_miner import BiorxivMiner
from miners.medrxiv_miner import MedrxivMiner
from miners.scielo_miner import ScieloMiner
from miners.preprints_miner import PreprintsMiner

class SiteWorkerIntegrated():
  '''
  SiteWorkerIntegrated class uses `site_worker_factory` method
  to send data mining request to a domain-specific SiteWorker
  given urls dataframe.

  Attributes:
    max_threshold (int): A default value of how many articles to upload
                          to a BigQuery table at a time.
    min_delay (int): A default value of min seconds to wait before the
                      next request to a website is sent.
    max_delay (int): A default value of max seconds to wait before the
                      next request to a website is sent.
  '''

  def __init__(self):
    self.max_threshold = 50
    self.min_delay = 0.1
    self.max_delay = 2
    self.article_schema = [
      {"name": "abstract",                  "type": "STRING",                    },
      {"name": "authors",                   "type": "STRING", "mode": "REQUIRED" },
      {"name": "body",                      "type": "STRING"                     },
      {"name": "category",                  "type": "STRING"                     },
      {"name": "date_aquisition",           "type": "DATE"                       },
      {"name": "date_publication",          "type": "DATE",   "mode": "REQUIRED" },
      {"name": "doi",                       "type": "STRING"                     },
      {"name": "extra_link",                "type": "STRING"                     },
      {"name": "keywords",                  "type": "STRING"                     },
      {"name": "license",                   "type": "STRING"                     },
      {"name": "organization_affiliated",   "type": "STRING"                     },
      {"name": "citations",                 "type": "STRING"                     },
      {"name": "references",                "type": "STRING"                     },
      {"name": "source",                    "type": "STRING"                     },
      {"name": "source_impact_factor",      "type": "STRING"                     },
      {"name": "title",                     "type": "STRING", "mode": "REQUIRED" },
      {"name": "url",                       "type": "STRING"                     }
    ]

  def send_request(self, urls_df, limit):
    ''' Finds domain from urls dataframe and sends request
    to a domain-specific SiteWorker using site_worker_factory class method.

    NOTE: An assumption is made that a given urls_dataframe contains
          urls from a single domain, thus `send_request` method
          checks only first entry in urls_dataframe 'article_url' field
          to find a domain.
    '''
    try:
        url = urls_df.at[0, 'article_url'] 
        domain = get_fld(url)
        print(domain)

        site_worker = self.site_worker_factory(domain, urls_df, limit, self.driver_path)
        site_worker.scrape_articles()
    
    except KeyError:
        print('The urls dataframe is empty')

  def scrape_data(self, miner, urls_df, article_schema, limit=100):
    ''' Scrapes data given urls' dataframe, and limit of articles to scrape.
    Uploads data to a given BigQuery table and calls `update_job_status` method
    from `JobDispatcher` class from `JobDispatcher` module
    to update `status` of the job to `done`.

    Attributes:
      urls_df (pandas dataframe): A urls dataframe, to get a list of
                                    article urls to scrape.
      limit (int): A limit of articles to scrape. Default is 100.
    '''

    urls = [url for url in list(urls_df['article_url'])]
    data = []
    prev_count = 0
    for count, url in enumerate(urls, 1):
      miner.gather(url)
      data.append(miner.results)
      if (count == self.max_threshold or count == limit or count == len(urls)):
        articles_list = list(filter(lambda i:
                            i['authors'] and i['date_publication'] and i['title'],
                            data[prev_count : count])) 
        articles_df = pd.DataFrame(articles_list)
        articles_df.to_gbq(destination_table=f'{self.article_table}',
                  project_id=self.project_id,
                  if_exists='append',
                  table_schema=article_schema,
                  credentials=self.credentials)
        JobDispatcher(self.credentials,
                      self.project_id,
                      self.url_table).update_job_status(urls_df.iloc[prev_count : count].copy())
        prev_count = count
      time.sleep(self.min_delay + self.max_delay * random.random())
    return articles_df
  
  @classmethod
  def init(cls, credentials, project_id, url_table, article_table, driver_path=None):
    ''' Initializes `SiteWorkerIngrated` class

    Attributes:
      credentials (str): Credentials, either from user_account or service_account,
                          to authenticate to Google Cloud APIs.
      project_id (str): A project_id on Google Cloud Platform.
      url_table (str): A url_table to use to retrieve urls_dataframe from,
                        in form of `dataset_id.table_id`.
      article_table (str): An article_table to use to upload scraped data to,
                        in form of `dataset_id.table_id`.
      driver_path (str): A driver path to a chromium-chromedriver.
    '''
    cls.credentials = credentials
    cls.project_id = project_id
    cls.url_table = url_table
    cls.article_table = article_table
    cls.driver_path = driver_path

  @classmethod
  def site_worker_factory(cls, domain_name, urls_df, limit=100, driver_path=None):
    ''' Sends a scraping request to a domain-specific SiteWorker

    Attributes:
      domain_name (str): A domain.
      urls_df (pandas dataframe): A urls dataframe.
      limit (int): A limit of articles to scrape. Default is 100.
      driver_path (str): A driver path to a chromium-chromedriver.
    '''
    site_worker = {'ibmc.msk.ru': IbmcRuSiteWorker(urls_df, limit, driver_path),
                   'arxiv.org': ArxivSiteWorker(urls_df, limit, driver_path),
                   'biorxiv.org': BiorxivSiteWorker(urls_df, limit, driver_path),
                   'medrxiv.org': MedrxivSiteWorker(urls_df, limit, driver_path),
                   'scielo.br': ScieloSiteWorker(urls_df, limit, driver_path),
                   'preprints.org': PreprintsSiteWorker(urls_df, limit, driver_path)
    }
    return site_worker[domain_name]

"""## Define IbmcRuSiteWorker class"""

class IbmcRuSiteWorker(SiteWorkerIntegrated):
  '''
  SiteWorker for http://pbmc.ibmc.msk.ru/

  Attributes:
    urls_df (pandas dataframe): A urls dataframe.
    limit (int): A limit of articles to scrape. Default is 100.
    driver_path (str): A driver path to a chromium-chromedriver.
    article_schema (list of dicts): An default article_schema for
                                      a given SiteWorker.
  '''
  def __init__(self, urls_df, limit=100, driver_path=None):
    super().__init__()
    self.urls_df = urls_df
    self.limit = limit
    self.driver_path = driver_path

  def scrape_articles(self):
    miner = IbmcRuMiner.IbmcEngine(IbmcRuMiner.IbmcLocations, driver_path=self.driver_path)
    self.scrape_data(miner, self.urls_df, self.article_schema, self.limit)

"""## Define ArxivSiteWorker class"""

class ArxivSiteWorker(SiteWorkerIntegrated):
  '''
  SiteWorker for https://arxiv.org/

  Attributes:
    urls_df (pandas dataframe): A urls dataframe.
    limit (int): A limit of articles to scrape. Default is 100.
    driver_path (str): A driver path to a chromium-chromedriver.
    article_schema (list of dicts): An default article_schema for
                                      a given SiteWorker.
  '''
  def __init__(self, urls_df, limit=100, driver_path=None):
    super().__init__()
    self.urls_df = urls_df
    self.limit = limit
    self.driver_path = driver_path

  def scrape_articles(self):
    miner = ArxivMiner.ArxivEngine(ArxivMiner.ArxivLocations, driver_path=self.driver_path)
    self.scrape_data(miner, self.urls_df, self.article_schema, self.limit)

"""## Define BiorxivSiteWorker class"""

class BiorxivSiteWorker(SiteWorkerIntegrated):
  '''
  SiteWorker for https://www.biorxiv.org/

  Attributes:
    urls_df (pandas dataframe): A urls dataframe.
    limit (int): A limit of articles to scrape. Default is 100.
    driver_path (str): A driver path to a chromium-chromedriver.
    article_schema (list of dicts): An default article_schema for
                                      a given SiteWorker.
  '''
  def __init__(self, urls_df, limit=100, driver_path=None):
    super().__init__()
    self.urls_df = urls_df
    self.limit = limit
    self.driver_path = driver_path

  def scrape_articles(self):
    miner = BiorxivMiner.BiorxivEngine(BiorxivMiner.BiorxivLocations, driver_path=self.driver_path)
    self.scrape_data(miner, self.urls_df, self.article_schema, self.limit)

"""## Define MedrxivSiteWorker class"""

class MedrxivSiteWorker(SiteWorkerIntegrated):
  '''
  SiteWorker for https://www.medrxiv.org/

  Attributes:
    urls_df (pandas dataframe): A urls dataframe.
    limit (int): A limit of articles to scrape. Default is 100.
    driver_path (str): A driver path to a chromium-chromedriver.
    article_schema (list of dicts): An default article_schema for
                                      a given SiteWorker.
  '''
  def __init__(self, urls_df, limit=100, driver_path=None):
    super().__init__()
    self.urls_df = urls_df
    self.limit = limit
    self.driver_path = driver_path
  
  def scrape_articles(self):
    miner = MedrxivMiner.MedrxivEngine(MedrxivMiner.MedrxivLocations, driver_path=self.driver_path)
    self.scrape_data(miner, self.urls_df, self.article_schema, self.limit)

"""## Define ScieloSiteWorker class"""

class ScieloSiteWorker(SiteWorkerIntegrated):
  '''
  SiteWorker for https://www.scielo.org/

  Attributes:
    urls_df (pandas dataframe): A urls dataframe.
    limit (int): A limit of articles to scrape. Default is 100.
    driver_path (str): A driver path to a chromium-chromedriver.
    article_schema (list of dicts): An default article_schema for
                                      a given SiteWorker.
  '''
  def __init__(self, urls_df, limit=100, driver_path=None):
    super().__init__()
    self.urls_df = urls_df
    self.limit = limit
    self.driver_path = driver_path
  
  def scrape_articles(self):
    miner = ScieloMiner.ScieloEngine(ScieloMiner.ScieloLocations, driver_path=self.driver_path)
    self.scrape_data(miner, self.urls_df, self.article_schema, self.limit)


"""## Define PreprintsSiteWorker class"""

class PreprintsSiteWorker(SiteWorkerIntegrated):
  '''
  SiteWorker for http://preprints.org/

  Attributes:
    urls_df (pandas dataframe): A urls dataframe.
    limit (int): A limit of articles to scrape. Default is 100.
    driver_path (str): A driver path to a chromium-chromedriver.
    article_schema (list of dicts): An default article_schema for
                                      a given SiteWorker.
  '''
  def __init__(self, urls_df, limit=100, driver_path=None):
    super().__init__()
    self.urls_df = urls_df
    self.limit = limit
    self.driver_path = driver_path

  def scrape_articles(self):
    miner = PreprintsMiner.PreprintsEngine(PreprintsMiner.PreprintsLocations, driver_path=self.driver_path)
    self.scrape_data(miner, self.urls_df, self.article_schema, self.limit)
