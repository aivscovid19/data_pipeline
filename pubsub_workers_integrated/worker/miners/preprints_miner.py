"""
Preprints miner by Yeshwanth R.
Edited by Gulnoza Kh. on 2020-12-17
"""

import centaurminer as mining


class PreprintsMiner:
    """
    Miner for https://preprints.org/
    """

    class PreprintsLocations(mining.PageLocations):
        abstract = mining.MetaData("og:description")
        keywords = mining.MetaData("citation_keywords")
        language = 'en'
        license = "https://creativecommons.org/licenses/by/4.0/"
        organization_affiliated = mining.MetaData("citation_author_institution")
        references = mining.MetaData("citation_reference")
        source = mining.MetaData('citation_publisher')

        # Null
        body = ''
        category = ''
        citations = ''
        search_keyword = ''
        source_impact_factor = ''

    class PreprintsEngine(mining.MiningEngine):
        def get_authors(self, element):
            return mining.TagList(self.get(element, several=True), tag='author')

        def get_organization_affiliated(self, element):
            return mining.TagList(self.get(element, several=True), tag='organization')

        def get_references(self, element):
            return self.get(element, several=True)
