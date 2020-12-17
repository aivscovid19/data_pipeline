"""
Arxiv miner by Yeshwanth R.
Edited by Gulnoza Kh. on 2020-11-09
"""

import centaurminer as mining


class ArxivMiner:
    """
    Miner for https://arxiv.org/
    """

    class ArxivLocations(mining.PageLocations):
        """
        This is a class used to find the schema in the journal
        """
        abstract = mining.Element("css_selector", "blockquote.abstract.mathjax")
        category = mining.Element("xpath", "//td[@class='tablecell subjects']")
        language = 'en'
        license = "https://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html"
        source = 'Arxiv'

        # Null:
        body = ''
        citations = ''
        keywords = ''
        organization_affiliated = ''
        references = ''
        search_keyword = ''
        source_impact_factor = ''

    class ArxivEngine(mining.MiningEngine):
        def get_authors(self, element):
            return mining.TagList(self.get(element, several=True), tag='author')

        def get_date_publication(self, element):
            """ Changes date format from YYYY/MM/DD to YYYY-MM-DD """
            date = self.get(element)
            if date is not None:
                return date.replace('/', '-')
            return date
