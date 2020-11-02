import centaurminer as mining
import json
import time

class ScieloLocations(mining.PageLocations):
    """Locations on the page to be gathered by Selenium webdriver
    
    The locations may be declared here as static variables of any type, to be retrieved
    as keys on the centaurminer.MiningEngine.results dictionary. Some examples of data that
    can be declared here:
    centaurminer.Metadata: Selenium retrieved elements from a page metadata
    centaurminer.Element: Selenium retrived elements from a page body.
    string: Strings declared here won't change, independently of the page searched.
    """

    source = mining.MetaData("citation_journal_title")
    date_publication = mining.Element("css_selector", "h3")
    body = mining.Element("css_selector", "#article-body, .index\,pt > p, .index\,en > p, .index\,es > p")
    abstract = mining.Element("css_selector", ".trans-abstract > p:not([class^=sec]), .trans-abstract > div.section")
    keywords = mining.Element("css_selector", ".trans-abstract > p:last-of-type")
    references = mining.Element("css_selector", "p.ref")
    organization_affiliated = mining.Element("css_selector", "p.aff").get_attribute('innerHTML')
    license = "https://scielo.org/en/about-scielo/open-access-statement/"
    pass

class ScieloEngine(mining.MiningEngine):
    """Mining Engine to get data from elements declared on centaurminer.PageLocations
    Here it's possible to process elements retrieved from centaurminer.PageLocations
    before gathering the results as a dictionary. To modify a specific element, declare
    a new method in the form get_<key>.
    Example:
        def get_authors(self, element):
            return TagList(self.get(element, several=True))
    """

    #########################
    ### Utilities Methods ###
    #########################
    
    @staticmethod
    def TagList(str_list, tag="item"):
        """ Returns a string from a joined list with elements separated by HTML-like tags
        Note:
            This method is overwritting base class centaurminer.MiningEngine
            default `CollectURLs` method.
        Args:
            str_list (list):     List of strings to be joined with HTML-like tags.
            tag (str, optional): Tag used to separate the elements in the form <></>  
        Returns:
            A string containing the list elements separated by HTML-like tags,
            None if str_list is None or empty.
        """
        if str_list:
            return ''.join(map(lambda s: f'<{tag}>{s.strip()}</{tag}>', str_list))
        return None

    @staticmethod
    def __format_author(author):
        """Formats a single author entry in full name format."""
        author = ' '.join(author.split(",")[::-1])
        return author.title().strip()

    @staticmethod
    def __parse_keywords(keys):
        """Extract keywords from HTML element"""
        key_strings = [ 
                    "keywords",
                    "key words",
                    "palavras-chave",
                    "palavras chave",
                    "index terms",
                    "descritores"
                  ]
        if not keys:
            return None
        for i in key_strings:
            if keys.lower().startswith(i):
                keys = keys[len(i):]
        return keys.replace(':', ' ').replace(';',',').split(',')

    ##################################
    ### Element Processing Methods ###
    ##################################


    def get_abstract(self, element):
        """Fetch abstract information from article URL."""
        return '\n'.join(self.get(element, several=True))


    def get_body(self, element):
        """Gather body text from article URL
        Note: 
            If body is retrieved from #article-body selector, it's safe
            to assume that it'll be pretty formatted. Otherwise, it's
            required to process <p> tags to retrieve body information.
        Args:
            element(:obj: `centaurminer.Element`): Page element to gather body data from.
        Return:
            String comprising whole body data
        """
        body = self.get(element, several=True)
        # Return if get from #article-body selector
        if len(body) == 1:
            return body[0]
        cleaned_paragraphs = []
        try:
            for idx, p in enumerate(body):
                if p.lower() in ["resumo", "abstract", "resumen"]:
                    abstract_index = idx
        # Clean up and join the paragraphs    
            for p in body[:abstract_index]:
                p = p.replace('&nbsp;',' ').strip()
                just_whitespace = all(char == " " for char in p)
                if not just_whitespace:
                    cleaned_paragraphs.append(p)
        except:
            pass
        if not len(cleaned_paragraphs):
            return None 
        return "\n".join(cleaned_paragraphs)


    def get_date_publication(self, element):
        """"Gather article date publication, in YYYY-MM-DD format
        Args:
            element(:obj: `centaurminer.Element`): Page element to
                gather body data from.
        Return:
            String representing date publication, in format YYYY-MM-DD.
        """
        try:
            date_str = str(self.get(element).split('Epub ')[1])
            try:
                date_obj = datetime.datetime.strptime(date_str, '%b %d, %Y')
            except ValueError:
                date_obj = datetime.datetime.strptime(date_str, '%B %d, %Y')          
            return date_obj.strftime('%Y-%m-%d')
        except (AttributeError, IndexError):
            element = mining.MetaData("citation_date")
            return self.get(element).replace('/', '-')
        except:
            return None
        #try:
        #    return str((self.get(element).split('Epub')[1]).date())
        #except (AttributeError, IndexError):
        #    return None

    def get_organization_affiliated(self, element):
        """Returns a string with article authors organizations, separated by HTML-like elements"""
        orgs = [o.split('</sup>')[-1] for o in self.get(element, several=True)]
        return self.TagList(orgs, "orgs")

    def get_references(self, element):
        """Returns a string with article references, separated by HTML-like elements"""
        reflist = self.get(element, several=True)
        refs = [r.replace('[ Links ]', '').strip('0123456789. ') for r in reflist]
        return self.TagList(refs)

    def get_authors(self, element):
        """Returns a string with article authors from search engine, separated by HTML-like elements"""
        authors = map(self.__format_author, self.get(element, several=True))
        return self.TagList(list(dict.fromkeys(authors)), 'author')

    def get_keywords(self, element):
        """Gather article keywords from centaurminer.Element object.
        Args:
            element(:obj: `centaurminer.Element`): Page element to gather keywords from.
        Returns:
            String comprising keywords separated by HTML-like tags.
        """
        keys = self.__parse_keywords(self.get(element))
        return self.TagList(keys, "keyword")

    def gather(self, url):
        """Retrieve mined information from a specific URL"""
        super().gather(url)
        self.results['acquisition_date'] = self.results.pop('date_aquisition')
        self.results['date']             = self.results.pop('date_publication')
        #self.results['pdf_link']         = self.results.pop('extra_link')
        self.results['link']             = self.results.pop('url')
        if not self.results['abstract']:
            self.results['abstract'] = self.results['body']
            if not self.results['abstract'] or not self.results['title']:
                self.results = None
        pass

def GetArticle(url):
    miner = ScieloEngine(ScieloLocations)
    miner.gather(url)
    
    # Mould results to match schema - move extra data to the meta_info column
    meta_info = {}
    keys = ['references', 'organization_affiliated', 'keywords', 'license', 'extra_link']
    for key in keys:
        if miner.results.get(key) is not None: # key exists and is non-None
            meta_info = miner.results.pop(key)
    #try:
    #    references = miner.results.pop('references')
    #    meta_info['references'] = references
    #except Exception as e:
    #    pass # Ignore this entry
    #try:
    #    orgs = miner.results.pop("organization_affiliated")
    #    meta_info['organization_affiliated'] = orgs
    #except Exception as e:
    #    pass # Ignore this entry
    #try:
    #    keywords = miner.results.pop("keywords")
    #    meta_info['keywords'] = keywords
    #except Exception as e:
    #    pass # Ignore this entry
    #try:
    #    license = miner.results.pop("license")
    #    meta_info['license'] = license
    #except Exception as e:
    #    pass # Ignore this entry
    #try:
    #    extra = miner.results.pop('extra_link')
    #    meta_info['pdf_link'] = extra
    #except Exception as e:
    #    pass # Ignore this entry

    miner.results['meta_info'] = json.dumps(meta_info)

    return miner.results
