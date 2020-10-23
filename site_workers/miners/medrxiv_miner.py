"""
Medrxiv miner by Yeshwanth R.
Edited by Gulnoza Kh. on 2020-10-20
"""

import centaurminer as mining

class MedrxivMiner():
  '''
  Miner for https://www.medrxiv.org/
  '''
  def __init__():
    pass

  class MedrxivLocations(mining.PageLocations):
    body = ''
    category = mining.Element("xpath", "//span[@class='highwire-article-collection-term']")
    citations = ''
    date_publication = mining.MetaData("article:published_time")
    keywords = ''
    license = mining.Element("xpath", "//div[@class='field-item even']")
    organization_affitiated = mining.MetaData("citation_author_institution")
    references = ''
    source = mining.MetaData("citation_journal_title")
    source_impact_factor = ''

  class MedrxivEngine(mining.MiningEngine):
    def get_authors(self, element):
      return mining.TagList(self.get(element, several=True),tag='author')

    def get_organization(self, element):
      return mining.TagList(self.get(element, several=True),tag='organization')

