from .ScieloBuilder import ScieloSearchLocations
from .ArxivBuilder import ArxivSearchLocations
import centaurminer as mining

def get(name):
    '''
    Switch which miner we're using based on the name.
    '''
    if name.lower() == "scielo":
        return ScieloBuilder.URLBuilder()
    elif name.lower() == "arxiv":
        return ArxivBuilder.URLBuilder()

    return None


class Scielo:
    '''
    Gathers URL links to articles on scielo.org.
    '''
    search_domain = 'https://search.scielo.org/'
    miner = mining.MiningEngine(ScieloSearchLocations)


class Arxiv:
    '''
    Gathers URL links to articles on artxiv.org.
    '''
    search_domain = 'https://export.arxiv.org/'
    miner = mining.MiningEngine(ArxivSearchLocations)

