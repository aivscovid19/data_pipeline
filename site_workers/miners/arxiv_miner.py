"""
Arxiv miner by Yeshwanth R.
Edited by Gulnoza Kh. on 2020-10-20
"""

import centaurminer as mining

class ArxivMiner():
  '''
  Miner for https://arxiv.org/
  '''
  def __init__():
    pass

  class ArxivLocations(mining.PageLocations):
    ''' 
      This is a class used to find the schema in the journal
    '''

    abstract = mining.Element("css_selector", "blockquote.abstract.mathjax")
    body = ''
    category = mining.Element("xpath", "//td[@class='tablecell subjects']")
    citations = ''
    keywords = ''
    license = "https://arxiv.org/licenses/nonexclusive-distrib/1.0/license.html"
    organization_affiliated = ''
    references = ''
    source = 'Arxiv'
    source_impact_factor = ''

  class ArxivEngine(mining.MiningEngine):
    def get_authors(self, element):
      return mining.TagList(self.get(element, several=True),tag='author')
    def get_date_publication(self, element):
      ''' Changes date format from YYYY/MM/DD to YYYY-MM-DD'''
      return (self.get(element).replace('/', '-'))

