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

    def scrape_data(self, miner, url):
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
        print(miner.results)

        time = datetime.min.time()
        data = {
            "abstract": miner.results['abstract'],
            "title": miner.results['title'],
            "authors": miner.results['authors'],
            "language": miner.results['language'],
            "doi": miner.results['doi'],
            "link": miner.results['url'],
            "source": miner.results['source'],
            "body": miner.results['body'],
            "publication_date": miner.results['date_publication'],
            # Dates are somewhat complicated - but this essentially just converts YYYY-MM-DD or YYYY/MM/DD
            # into a datetime object (at midnight)
            "acquisition_date": datetime.combine(date(*[int(x) for x in miner.results['date_aquisition'].split("-")]), time),
        }
        # if miner.results['date_publication'] is not None:
        #    data["publication_date"] = datetime.combine(date(*[int(x) for x in miner.results['date_publication'].split("-")]), time)

        # Add the meta info
        meta_info = {
            "references:": miner.results['references'],
            "search_keyword": miner.results['search_keyword'],
            "license": miner.results['license'],
            "extra_link": miner.results['extra_link']
        }

        data['meta_info'] = json.dumps(meta_info)
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
        miner = ScieloMiner.ScieloEngine(ScieloMiner.ScieloLocations, driver_path=self.driver_path)
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
