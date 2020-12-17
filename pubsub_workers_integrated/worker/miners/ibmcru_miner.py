"""
IbmcRu miner by Gulnoza Kh.
Edited by Gulnoza Kh. on 2020-11-09
"""

import centaurminer as mining


class IbmcRuMiner:
    """
    Miner for http://pbmc.ibmc.msk.ru/
    """

    class IbmcLocations(mining.PageLocations):
        """
        IbmcLocations class sets instructions to find an element on
        `http://pbmc.ibmc.msk.ru/`
        """
        abstract = mining.Element("xpath", "//td[@class='arti'][@style='text-align:justify;']")
        category = mining.Element("xpath", "//tr[4]/td[@class='arti']")
        citations = mining.Element("xpath", "//div[@class='__db_score __db_score_normal']")
        keywords = mining.MetaData("citation_keywords")
        license = "http://pbmc.ibmc.msk.ru/ru/authors-rules-ru/"
        organization_affiliated = mining.MetaData("citation_author_institution")
        source = mining.MetaData("citation_journal_title")
        language = 'ru'
        # pubmed_link = mining.Element("xpath", "//td[@class='arti'][@style='align:justify;']//a[@target='_blank']").get_attribute('href')
        # translated_link = mining.Element("xpath", "//td[@class='arti']//a[@target='_blank']").get_attribute('href')

        # Null:
        body = ''
        references = ''
        source_impact_factor = ''
        search_keyword = ''

    class IbmcEngine(mining.MiningEngine):
        """
        IbmcEngine class sets instructions on how to mine data from
        `http://pbmc.ibmc.msk.ru/`
        """

        def get_authors(self, element):
            """ Gets several `author` fields and wraps them inside
            `html` like tags. """
            return mining.TagList(self.get(element, several=True), tag='author')

        def get_date_publication(self, element):
            """ Changes date format from YYYY/MM/DD to YYYY-MM-DD """
            return self.get(element).replace('/', '-')

        def get_organization_affiliated(self, element):
            """
            Gets several `organizations_affiliated` fields and wraps them
            inside `html` like tags.
            """
            return mining.TagList(self.get(element, several=True), tag='org')
