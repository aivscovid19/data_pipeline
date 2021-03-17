import json
from tld import get_fld
from datetime import datetime, date

from miners import ArxivMiner
from miners import BiorxivMiner
from miners import IbmcRuMiner
from miners import MedrxivMiner
from miners import PreprintsMiner
from miners import ScieloMiner

class MinerNotFoundError(Exception):
    pass

class SiteWorkerIntegrated:
    """
    SiteWorkerIntegrated class uses `site_worker_factory` method
    to send data mining request to a domain-specific SiteWorker
    given urls dataframe.

    Attributes:
        driver_path(str): A path to a chromium webdriver. Default is None
        max_threshold (int): A default value of how many articles to upload
                          to a BigQuery table at a time.
        min_delay (int): A default value of min seconds to wait before the
                      next request to a website is sent.
        max_delay (int): A default value of max seconds to wait before the
                      next request to a website is sent.
    """
    def __init__(self, driver_path=None):
        self.driver_path = driver_path
        self.max_threshold = 50
        self.min_delay = 0.1
        self.max_delay = 2

    def send_request(self, url):
        """
        Finds domain from urls dataframe and sends request
        to a domain-specific SiteWorker using site_worker_factory class method.

        Attributes:
            url (str): An article url.

        Returns:
            (dictionary): Scraped data in form of a dictionary.
        """
        domain = get_fld(url)
        site_worker = self.site_worker_factory(domain, url, self.driver_path)
        return site_worker.scrape_articles()

    @staticmethod
    def scrape_data(miner, url):
        """
        Scrapes data given urls' dataframe, and limit of articles to scrape.
        Uploads data to a given BigQuery table and calls `update_job_status` method
        from `JobDispatcher` class from `JobDispatcher` module
        to update `status` of the job to `done`.

        Attributes:
            url (str): An article url.

        Returns:
            data(dictionary): Scraped data in form of dictionary.
        """
        miner.gather(url)

        data_map = {
            "abstract": 'abstract',
            "title": 'title',
            "authors": 'authors',
            "language": 'language',
            "doi": 'doi',
            "link": 'url',
            "source": 'source',
            "body": 'body',
            "publication_date": 'date_publication',
            "acquisition_date": 'date_aquisition' # Note the typo - this will be fixed in centaurminer > 0.1.0
        }
        # Select relevant data using the map
        data = {}
        for key, val in data_map.items():
            data[key] = miner.results.get(val)

        # special case for the acquisition date (which WILL be fixed in a future version of centaurminer)
        # Justs adds a time (midnight) and converts a string into a datetime object
        time = datetime.min.time()
        data["acquisition_date"] = datetime.combine(date(*[int(x) for x in data['acquisition_date'].split("-")]), time),

        # Add the meta info
        meta_info = {}
        for key, val in miner.results.items():
            if key not in data_map.values():
                meta_info[key] = miner.results[key]

        data['meta_info'] = json.dumps(meta_info, ensure_ascii=False, default=repr)
        return data

    @classmethod
    def site_worker_factory(cls, domain_name, url, driver_path=None):
        """ Sends a scraping request to a domain-specific SiteWorker

        Attributes:
            domain_name (str): A domain.
            url (str): An article url.
            driver_path (str): A driver path to a chromium-chromedriver.
        """
        site_worker = {'ibmc.msk.ru': IbmcRuSiteWorker(url, driver_path),
                       'arxiv.org': ArxivSiteWorker(url, driver_path),
                       'biorxiv.org': BiorxivSiteWorker(url, driver_path),
                       'medrxiv.org': MedrxivSiteWorker(url, driver_path),
                       'scielo.br': ScieloSiteWorker(url, driver_path),
                       'sld.cu': ScieloSiteWorker(url, driver_path),
                       'preprints.org': PreprintsSiteWorker(url, driver_path)
                       }
        try:
            return site_worker[domain_name]
        except KeyError as e:
            raise MinerNotFoundError(f"The miner you requested ({domain_name}) does not exist")


""" Site Workers """
""" Define IbmcRuSiteWorker class """


class IbmcRuSiteWorker(SiteWorkerIntegrated):
    """
    SiteWorker for http://pbmc.ibmc.msk.ru/

    Attributes:
       url (str): An article url.
       driver_path (str): A driver path to a chromium-chromedriver. Default is None.
    """
    def __init__(self, url, driver_path=None):
        super().__init__()
        self.url = url
        self.driver_path = driver_path

    def scrape_articles(self):
        miner = IbmcRuMiner.IbmcEngine(IbmcRuMiner.IbmcLocations, driver_path=self.driver_path)
        return self.scrape_data(miner, self.url)


""" Define ArxivSiteWorker class """


class ArxivSiteWorker(SiteWorkerIntegrated):
    """
    SiteWorker for https://arxiv.org/

    Attributes:
        url (str): An article url.
        driver_path (str): A driver path to a chromium-chromedriver. DEfault is None.
    """
    def __init__(self, url, driver_path=None):
        super().__init__()
        self.url = url
        self.driver_path = driver_path

    def scrape_articles(self):
        miner = ArxivMiner.ArxivEngine(ArxivMiner.ArxivLocations, driver_path=self.driver_path)
        return self.scrape_data(miner, self.url)


""" Define BiorxivSiteWorker class """


class BiorxivSiteWorker(SiteWorkerIntegrated):
    """
    SiteWorker for https://www.biorxiv.org/

    Attributes:
        url (str): An article url.
        driver_path (str): A driver path to a chromium-chromedriver. Default is None.
    """
    def __init__(self, url, driver_path=None):
        super().__init__()
        self.url = url
        self.driver_path = driver_path

    def scrape_articles(self):
        miner = BiorxivMiner.BiorxivEngine(BiorxivMiner.BiorxivLocations, driver_path=self.driver_path)
        return self.scrape_data(miner, self.url)


""" Define MedrxivSiteWorker class """


class MedrxivSiteWorker(SiteWorkerIntegrated):
    """
    SiteWorker for https://www.medrxiv.org/

    Attributes:
        url (str): An article url.
        driver_path (str): A driver path to a chromium-chromedriver. Default is None.
    """
    def __init__(self, url, driver_path=None):
        super().__init__()
        self.url = url
        self.driver_path = driver_path
  
    def scrape_articles(self):
        miner = MedrxivMiner.MedrxivEngine(MedrxivMiner.MedrxivLocations, driver_path=self.driver_path)
        return self.scrape_data(miner, self.url)


""" Define ScieloSiteWorker class """


class ScieloSiteWorker(SiteWorkerIntegrated):
    """
    SiteWorker for https://www.scielo.org/

    Attributes:
        url (str): An article url.
        driver_path (str): A driver path to a chromium-chromedriver. Default is None.
    """
    def __init__(self, url, driver_path=None):
        super().__init__()
        self.url = url
        self.driver_path = driver_path
  
    def scrape_articles(self):
        '''
        There are several formats for scielo.br articles - choose a different miner for each.
        '''
        # Just get any webdriver to start, since we need to find elements on the page
        from centaurminer import MiningEngine, PageLocations
        wd = MiningEngine(PageLocations).wd
        wd.get(self.url)

        # Look for key elements that define the different formats
        miner = None
        if wd.find_elements_by_id('article-body'):
            print("Detected fully structured article")
            miner = ScieloMiner.ScieloEngineStructured(ScieloMiner.ScieloLocationsStructured, driver_path=self.driver_path)
        elif wd.find_elements_by_css_selector('.index\,pt, .index\,en, .index\,es'):
            print("Detected flat article")
            miner = ScieloMiner.ScieloEngineFlat(ScieloMiner.ScieloLocationsFlat, driver_path=self.driver_path)
        else:
            print("idk, tell me more about this format")
            print(wd.page_source)
            miner = ScieloMiner.ScieloEngine(ScieloMiner.ScieloLocations, driver_path = self.driver_path)
        return self.scrape_data(miner, self.url)


""" Define PreprintsSiteWorker class """


class PreprintsSiteWorker(SiteWorkerIntegrated):
    """
    SiteWorker for http://preprints.org/

    Attributes:
        url (str): An article url.
        driver_path (str): A driver path to a chromium-chromedriver. Default is None.
    """
    def __init__(self, url, driver_path=None):
        super().__init__()
        self.url = url
        self.driver_path = driver_path

    def scrape_articles(self):
        miner = PreprintsMiner.PreprintsEngine(PreprintsMiner.PreprintsLocations, driver_path=self.driver_path)
        return self.scrape_data(miner, self.url)

if __name__ == "__main__":
    # Scrape a site given as a command line arg
    from sys import argv
    assert len(argv) == 2, "Must include a URL"

    print(argv[1])
    data = SiteWorkerIntegrated().send_request(argv[1])
    print(*data.items(), sep="\n\n")
