import time
import pandas_gbq
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account

from urlbuilder import URLBuilder as ScieloURLBuilder
from urlbuilder import ScieloSearchLocations

import centaurminer as mining
import os

class URL_builder():
  """
    URL_builder class uses `urlbuilderfactory` method
    to extract URLs from a specific journal.

    ...

    Attributes
    ----------
    search_word (str): word to be searched

    Methods
    -------
    url_collector(): Scrapes URLs from the pages.
    create_url_schema(list_of_urls,catalog_url,is_pdf,lang): Create url schema to push into bigquery.
    send_to_bigquery(project_id,table_id): To push url_schema to bigquery.
    
  """
  
  def __init__(self,search_word):
    """
        Constructs all the necessary attributes for the URL_builder object.

        Parameters
        ----------
            search_word(str): word to be searched
        """
    self._url_list=[]
    self.total_urls=[]
    self.valid_urls=[]
    self._search_word=search_word
    self.urls_dataframe = pd.DataFrame()
    self._driver_path = '/usr/lib/chromium-browser/chromedriver'
    self._anchor_element={'arxiv':'span.list-identifier > a',
                          'biorxiv':'a.highwire-cite-linked-title',
                          'medrxiv':'a.highwire-cite-linked-title',
                          'preprint':'a#title.title',
                          'pbmc':'a.class1','jamanetwork':'h3.article--title > a'}

    self._url_base={'arxiv':f"http://export.arxiv.org/find/all/1/all:+{search_word}/0/1/0/all/0/1?skip=".format(search_word),
              'biorxiv':f'https://www.biorxiv.org/search/{search_word}%20numresults%3A75%20sort%3Apublication-date%20direction%3Adescending?page='.format(search_word),
              'medrxiv':f'https://www.medrxiv.org/search/{search_word}%20numresults%3A75%20sort%3Apublication-date%20direction%3Adescending?page='.format(search_word),
              'preprint':f"https://www.preprints.org/search?search1={search_word}&field1=article_abstract&field2=authors&clause=AND&search2=&page_num=".format(search_word),
              'pbmc':f'http://pbmc.ibmc.msk.ru/ru/search-ru/?search={search_word}&fn=5'.format(search_word),
              'jamanetwork':f'https://jamanetwork.com/searchresults?q={search_word}&sort=Newest&page='.format(search_word)
              }


    self._schema = [
            {'name': 'article_url', 'type': 'STRING',    'mode': 'REQUIRED'},
            {'name': 'catalog_url', 'type': 'STRING',    'mode': 'REQUIRED'},
            {'name': 'is_pdf',      'type': 'INTEGER',   'mode': 'REQUIRED'},
            {'name': 'language',    'type': 'STRING',                      },
            {'name': 'status',      'type': 'STRING',    'mode': 'REQUIRED'},
            {'name': 'timestamp',   'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
            {'name': 'worker_id',   'type': 'STRING',                      },
            {'name': 'meta_info',   'type': 'STRING',                      },
    ]
  



  @classmethod
  def connect_to_gbq(cls,project_id,table_id):
    """ 
      Establish a connection with Google BigQuery
        Args:
            project_id (string): Google Cloud project ID.
            table_id (string): Table information to read and write data on.
                Must be specified as `<dataset_name>.<table_name>`.
        Example:
            URL_builder.connect_to_gbq('for-yr','my_dataset.my_table').
        Auth_docs:
            Reference for Google BigQuery Authentication, on this context:
            'https://pandas-gbq.readthedocs.io/en/latest/howto/authentication.html'
    """
    cls.project_id=project_id
    cls.table_id=table_id



  @classmethod
  def urlbuilderfactory(cls,journal_name,search_word,limit,time_frame):
    '''
      Scrapes URLs from given journal name.
        Args:
            journal_name(str): Name of the journal from which URLs need to be scraped.
            search_word(str): keyword to be searched.
            limit(int): number of URLs to be scraped.
            time_frame(float): waiting time period to send dataframe to bigquery.
        Example:
            URL_builder.urlbuilderfactory('arxiv','virus',1000,10)
    '''
    journaldictionary={'arxiv':arxiv_url(search_word,limit,time_frame),
                       'preprint':preprint_url(search_word,limit,time_frame),
                       'biorxiv':biorxiv_url(search_word,limit,time_frame),
                       'medrxiv':medrxiv_url(search_word,limit,time_frame),
                       'pbmc':pbmc_url(search_word,limit,time_frame),
                       'scielo':scielo_url(search_word,limit,time_frame),
                       'jamanetwork': jamanetwork_url(search_word,limit,time_frame)
                       }
    return journaldictionary[journal_name]

  


  def _url_collector(self):
    '''
      Method to scrape the article URLs from a given page.
    '''
    if self.page_num is not None:
      self.page_url=self._url_base[self.journal]+str(self.page_num)
    else:
      self.page_url=self._url_base[self.journal]
    articles = mining.Element("css_selector",self._anchor_element[self.journal]).get_attribute('href')
    self.urls = mining.CollectURLs(self.page_url, articles, driver_path=self._driver_path)  
  

  
  
  def _create_url_schema(self,list_of_urls,catalog_url,is_pdf=None,lang='en'):
    '''
      Method to create a dataframe for a set of urls.

      Args:
        list_of_urls(list): URLs scraped.
        url(str): catalog URL
        is_pdf: Function to determine if the URL is PDF or not.
        lang(str): language of the data.

      Returns:
        Dataframe
    '''
    self._url_schema=pd.DataFrame({'article_url': list_of_urls})
    self._url_schema['catalog_url']=catalog_url
    if is_pdf==None:
      self._url_schema['is_pdf'] =0
    else:
      self._url_schema['is_pdf'] = self._url_schema['article_url'].apply(is_pdf)
    self._url_schema['language']=lang
    self._url_schema['status']='Not Mined'
    self._url_schema['timestamp']= datetime.utcnow()
    self._url_schema['worker_id']=None
    self._url_schema['meta_info']=None
    return self._url_schema
  
  
 

    
  def _send_to_bigquery(self):
    '''
        Method to send dataframe to bigquery.
    '''
    pandas_gbq.to_gbq(self.urls_dataframe, self.table_id, project_id=self.project_id, if_exists='append', table_schema=self._schema)
    pass
  



  def get_urls(self):
    '''
      Method to get URLs and send url_schema to bigquery.
    '''
    self.page_num=0
    start_time=time.time()
    check_urls=[]
    while self.page_num >=0:
      print(f"\n Scraping from page...", flush=True)
      self._url_collector()

      [self.valid_urls.append(i) for i in self.urls]  
      nums=min(self.limit - len(self.total_urls), len(self.urls))
      self.total_urls.extend(self.valid_urls[:nums])    
      self._url_list=[]
      [self._url_list.append(i) for i in self.urls[:nums]]
      self._create_url_schema(self._url_list,self.page_url)
    

      self.urls_dataframe = pd.concat([self.urls_dataframe,self._url_schema],ignore_index=True)
      if (time.time()-start_time)>=self.time_frame:
        print('\n Sending URLs to BigQuery')
        self._send_to_bigquery()
        self.urls_dataframe=pd.DataFrame()
        start_time=time.time()
        
      if len(self.total_urls) == self.limit:
        break
      self.page_num+=1

    self._send_to_bigquery()
    print('\n Total no. of URLS sent to BigQuery:'+str(len(self.total_urls)))






class arxiv_url(URL_builder):
  """
      Child class for getting URLs from arxiv journal.
      Arxiv: http://export.arxiv.org/

      Args:
        search_word(str): word to be searched
        limit(int): number of URLs to be collected
        time_frame(float): waiting time period to send dataframe to bigquery
  """

  def __init__(self,search_word,limit,time_frame):
        super().__init__(search_word)  
        self.limit=limit
        self.time_frame=time_frame
        self.journal='arxiv'
  

  def get_urls(self):
    '''
      Method to get URLs and send url_schema to bigquery.

      Returns: url_schema

    '''
    self.page_num=0
    start_time=time.time()
    while self.page_num>=0:    
      self.valid_urls=[]
      print(f"\n Scraping from page {self.page_num}...", flush=True)
      is_pdf = lambda x: pd.Series({'is_pdf': 1 if x.find('pdf') != -1 else 0}) 
      self._url_collector()

      [self.valid_urls.append(i) for i in self.urls if 'format' not in i]   
      nums=min(self.limit - len(self.total_urls), len(self.valid_urls))
      self.total_urls.extend(self.valid_urls[:nums])
      self._url_list=[]
      [self._url_list.append(i) for i in self.valid_urls[:nums]]
      self._create_url_schema(self._url_list,self.page_url,is_pdf)


      self.urls_dataframe = pd.concat([self.urls_dataframe,self._url_schema],ignore_index=True)
      if (time.time()-start_time)>=self.time_frame:
        print('\n Sending URLs to BigQuery')
        self._send_to_bigquery()
        self.urls_dataframe=pd.DataFrame()
        start_time=time.time()

      
      self.page_num+=25      
      if len(self.total_urls) == self.limit:
        break

    self._send_to_bigquery()
    print('\n Total no. of URLS sent to BigQuery:'+str(len(self.total_urls)))




class preprint_url(URL_builder):
  """
      Child class for getting URLs from preprint journal.
      Preprint: https://www.preprints.org/

      Args:
        search_word(str): word to be searched
        limit(int): number of URLs to be collected
        time_frame(float): waiting time period to send dataframe to bigquery
  """

  def __init__(self,search_word,limit,time_frame):
      super().__init__(search_word)  
      self.limit=limit
      self.time_frame=time_frame
      self.journal='preprint'
  
    



class biorxiv_url(URL_builder):
  """
      Child class for getting URLs from preprint journal.
      Biorxiv: https://www.biorxiv.org/

      Args:
        search_word(str): word to be searched
        limit(int): number of URLs to be collected
        time_frame(float): waiting time period to send dataframe to bigquery
  """

  def __init__(self,search_word,limit,time_frame):
      super().__init__(search_word)  
      self.limit=limit
      self.time_frame=time_frame
      self.journal='biorxiv'
  
  


class medrxiv_url(URL_builder):
  """
      Child class for getting URLs from preprint journal.
      Medrxiv: https://www.medrxiv.org/

      Args:
        search_word(str): word to be searched
        limit(int): number of URLs to be collected
        time_frame(float): waiting time period to send dataframe to bigquery
  """

  def __init__(self,search_word,limit,time_frame):
      super().__init__(search_word)  
      self.limit=limit
      self.time_frame=time_frame
      self.journal='medrxiv'  


class jamanetwork_url(URL_builder):
  """
      Child class for getting URLs from preprint journal.
      pbmc: https://jamanetwork.com/

      Args:
        search_word(str): word to be searched
        limit(int): number of URLs to be collected
        time_frame(float): waiting time period to send dataframe to bigquery
  """

  def __init__(self,search_word,limit,time_frame):
      super().__init__(search_word)  
      self.limit=limit
      self.time_frame=time_frame
      self.journal = 'jamanetwork'
  

class pbmc_url(URL_builder):
  """
      Child class for getting URLs from preprint journal.
      pbmc: http://pbmc.ibmc.msk.ru/

      Args:
        search_word(str): word to be searched
        limit(int): number of URLs to be collected
        time_frame(float): waiting time period to send dataframe to bigquery
  """

  def __init__(self,search_word,limit,time_frame):
    super().__init__(search_word)
    self.limit=limit
    self.time_frame=time_frame
    self.journal='pbmc'
    
  
  def get_urls(self):
    '''
      Method to get URLs and send url_schema to bigquery.

      Returns: url_schema
    '''
    self.page_num=None
    print(f"\n Scraping from page...", flush=True)
    self._url_collector()
    [self.valid_urls.append(i) for i in self.urls if 'article-ru' in i]  
    nums=min(self.limit - len(self.total_urls), len(self.valid_urls))
    self.total_urls.extend(self.valid_urls[:nums])
    [self._url_list.append(i) for i in self.valid_urls[:nums]]
    self._create_url_schema(self._url_list,self.page_url,lang='ru')
    self.urls_dataframe = pd.concat([self.urls_dataframe,self._url_schema],ignore_index=True)
    self._send_to_bigquery()
    print('\n Total no. of URLS sent to BigQuery:'+str(len(self.total_urls))) 

class scielo_url(URL_builder):
  """
      Child class for getting URLs from preprint journal.
      scielo: https://search.scielo.org/

      Args:
        search_word(str): word to be searched
        limit(int): number of URLs to be collected
        time_frame(float): waiting time period to send dataframe to bigquery
  """

  def __init__(self,search_word,limit,time_frame):
    super().__init__(search_word)
    self.limit=limit
    self.time_frame=time_frame

  def get_urls(self):
    '''
      Method to get URLs and send url_schema to bigquery.

      Returns: url_schema
    '''
    print('scielo')
    miner = mining.MiningEngine(ScieloSearchLocations, driver_path=self._driver_path)
    ScieloURLBuilder.connect_to_gbq(self.credentials, self.project_id, self.table_id, self._schema)
    scielo_builder = ScieloURLBuilder(miner)
    scielo_builder.collect('https://search.scielo.org/', self._search_word, self.limit)


    
    
    
if __name__ == "__main__":
    domain       = os.environ["DOMAIN"]
    project_id   = os.environ["PROJECT_ID"]
    url_table_id = os.environ["TABLE_ID"]
    search_item  = os.environ["SEARCH_WORD"]
    limit        = int(os.environ["LIMIT"])
    time_frame   = float(os.environ["TIME_FRAME"])

    URL_builder.connect_to_gbq(project_id, url_table_id)

    url=URL_builder.urlbuilderfactory(domain,search_item,limit,time_frame)
    url.get_urls()
