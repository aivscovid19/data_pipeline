"""
Medrxiv miner by Yeshwanth R.
Edited by Gulnoza Kh. on 2020-11-09
"""

import centaurminer as mining


class MedrxivMiner:
    """
    Miner for https://www.medrxiv.org/
    """

    class MedrxivLocations(mining.PageLocations):
        category = mining.Element("xpath", "//span[@class='highwire-article-collection-term']")
        date_publication = mining.MetaData("article:published_time")
        language = 'en'
        license = mining.Element("xpath", "//div[@class='field-item even']")
        organization_affiliated = mining.MetaData("citation_author_institution")
        source = mining.MetaData("citation_journal_title")

        # Null
        body = ''
        citations = ''
        keywords = ''
        references = ''
        search_keyword = ''
        source_impact_factor = ''

    class MedrxivEngine(mining.MiningEngine):
        def get_authors(self, element):
            return mining.TagList(self.get(element, several=True), tag='author')

        def get_organization(self, element):
            return mining.TagList(self.get(element, several=True), tag='organization')
