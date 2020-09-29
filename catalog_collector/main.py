#!/usr/bin/env python

from collector import ScieloSearchLocations
from collector import CatalogCollector
import centaurminer as mining
import redis
import sys
#import os

def parse_args(argv):
    """Prepare arguments before sending to program logic"""

    if len(sys.argv) <= 1:
        print("There's no parameters, getting out right now")
        sys.exit(0)
    search_terms = argv[1::]
    try:
        limit = int(argv[-1])
    except ValueError:
        limit = None
    else:
        search_terms.pop()
    return search_terms, limit



def main():

    r = redis.Redis(host='redis-server', port=6379, db=0)
    driver_path='/usr/lib/chromium-browser/chromedriver'
    miner = mining.MiningEngine(ScieloSearchLocations, driver_path=driver_path)
    scielo_collector = CatalogCollector(miner)

    # Collect search pages and send them to Redis Pub/Sub queue
    search_domain = 'https://search.scielo.org/'
    search_terms, limit = parse_args(sys.argv)
    url_list = scielo_collector(search_domain, search_terms, limit)
    r.lpush("search_pages", *url_list)



if __name__  == "__main__":
    main()
