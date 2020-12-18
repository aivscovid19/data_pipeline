"""
Biorxiv miner by Yeshwanth R.
Edited by Gulnoza Kh. on 2020-12-17
"""

import centaurminer as mining


class BiorxivMiner:
    """
    Miner for https://www.biorxiv.org/
    """

    class BiorxivLocations(mining.PageLocations):
        """ This is a class used to find the schema in the journal """
        category = mining.Element("xpath", "//span[@class='highwire-article-collection-term']")
        language = 'en'
        license = mining.Element("xpath", "//div[@class='field-item even']")
        organization_affiliated = mining.MetaData("citation_author_institution")
        references = mining.MetaData("citation_reference")
        source = mining.MetaData("citation_journal_title")

        # Null:
        body = ''
        citations = ''
        keywords = ''
        search_keyword = ''
        source_impact_factor = ''

    class BiorxivEngine(mining.MiningEngine):
        def get_authors(self, element):
            return mining.TagList(self.get(element, several=True), tag='author')
      
        def get_organization_affiliated(self, element):
            return mining.TagList(self.get(element, several=True), tag='organization')

        def get_references(self, element):
            return self.get(element, several=True)
