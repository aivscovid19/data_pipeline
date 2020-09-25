import centaurminer as mining
import json
from datetime import datetime, date


class Arxiv(mining.PageLocations):
    """
    This is a class used to find the schema in the journal
    """
    references = mining.MetaData("")
    title = mining.MetaData("citation_title")
    doi = mining.MetaData("citation_doi")
    authors = mining.MetaData("citation_author")
    abstract = mining.Element("css_selector", "blockquote.abstract.mathjax")
    body = mining.MetaData("")
    source_impact_factor = mining.MetaData("")
    category = mining.MetaData("")
    quantity_of_citations = mining.MetaData("")
    organization = mining.MetaData("")
    keywords = mining.MetaData("")
    extra_link = mining.MetaData("citation_pdf_url")

    # Constants
    source = 'Arxiv'
    language = "english"
    license = "https://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html"
    search_keyword = "SARS"


class Arxiveng(mining.MiningEngine):
    def get_authors(self, element):
        return mining.TagList(self.get(element, several=True), tag='author')


def GetArticle(url):
    miner = Arxiveng(Arxiv)
    miner.gather(url)

    # Convert results to match the required bigquery schema
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
        # Dates are somewhat complicated - but this essentially just converts YYYY-MM-DD or YYYY/MM/DD into a datetime object (at midnight)
        "acquisition_date": datetime.combine(date(*[int(x) for x in miner.results['date_aquisition'].split("-")]), time),
    }
    if miner.results['date_publication'] is not None:
        data["publication_date"] = datetime.combine(date(*[int(x) for x in miner.results['date_publication'].split("/")]), time)

    # Add the meta info
    meta_info = {
        "references:": miner.results['references'],
        "search_keyword": miner.results['search_keyword'],
        "license": miner.results['license'],
        "extra_link": miner.results['extra_link']
    }

    data['meta_info'] = json.dumps(meta_info)
    return data
