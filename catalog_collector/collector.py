#!/usr/bin/python3

from urllib import parse
import centaurminer as mining
import math
import time

class ScieloSearchLocations(mining.PageLocations):
    """HTML locations on the earch page to be gathered by centaurminer"""

    link_elem = mining.Element('css_selector', 'a.showTooltip').get_attribute('href')
    finish = mining.Element("css_selector", "div.midGlyph.alert")
    total_hits = mining.Element("css_selector", "#TotalHits")
    pass


class CatalogCollector():
    """Create lists of search pages URLs to be processed with an article URL Builder"""

    def __init__(self, miner):
        """ URLBuilder constructor
        Args:
            miner (:obj: `centaurminer.Mining`): Mining Engine
            based on centaurMiner project.
        """
        self.miner = miner
        pass
    
    def __call__(self, domain, keywords, limit=None):
        """Collect article URLS and send them to Redis Pub/Sub queue.

        Args:
            domain (str):
                Default search page from website.
            keywords (`list` of `str`):
                List of keywords to search from domain.
            limit (int):
                Max number of pages to include in BigQuery.
        Returns:
            List of search result URLs collected during this process.
        """
        return self._collect(domain, keywords, limit)

    def _collect(self, domain, keywords, limit=None):
        """Collect article URLS and send them to Redis Pub/Sub queue.

        Args:
            domain (str):
                Default search page from website.
            keywords (`list` of `str`):
                List of keywords to search from domain.
            limit (int):
                Max number of pages to include in BigQuery.
        Returns:
            List of search result URLs collected during this process.
        """

        count = 0
        URLS_PER_PAGE = 15 # Can be changed to 15, 30 or 50

        # Gather search meta information: max number of results
        # and max number of pages
        self.miner.wd.get(self._search_url(domain, keywords))
        total_hits = int(self.miner.get(self.miner.site.total_hits).replace(' ', ''))
        total = total_hits if limit is None or limit > total_hits else limit
        n_pages = math.ceil(total / URLS_PER_PAGE)
        #for i in range(n_pages):
        #    source_page = self._search_url(domain, keywords, i + 1)
        #    print(source_page)
        return [self._search_url(domain, keywords, i + 1) for i in range(n_pages)]


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
