"""
Scielo miner by Adrian R.
Edited by Gulnoza Kh. on 2020-12-17
"""

import centaurminer as mining
import datetime


class ScieloMiner:
    """
    Miner for https://scielo.org
    """

    class ScieloLocations(mining.PageLocations):
        """Locations on the page to be gathered by Selenium webdriver

        The locations may be declared here as static variables of any type, to be retrieved
        as keys on the centaurminer.MiningEngine.results dictionary. Some examples of data that
        can be declared here:

        centaurminer.Metadata: Selenium retrieved elements from a page metadata
        centaurminer.Element: Selenium retrived elements from a page body.
        string: Strings declared here won't change, independently of the page searched.
        """
        abstract = mining.Element("css_selector", ".trans-abstract > p:not([class^=sec]), .trans-abstract > div.section")
        body = mining.Element("css_selector", "#article-body, .index\,pt > p, .index\,en > p, .index\,es > p")
        category = mining.Element("xpath", "//p[@class='categoria']")
        date_publication = mining.Element("xpath", "//div[@class='content']/h3")
        keywords = mining.Element("css_selector", ".trans-abstract > p:last-of-type")
        language = mining.MetaData("citation_language")
        license = "https://scielo.org/en/about-scielo/open-access-statement/"
        organization_affiliated = mining.Element("css_selector", "p.aff").get_attribute('innerHTML')
        references = mining.Element("css_selector", "p.ref")
        source = mining.MetaData("citation_journal_title")
        title = mining.Element("css_selector", "p.title")

        # addition to meta-info:
        title_translated = mining.Element("css_selector", "p.trans-title")
        abstract_translated = mining.Element("css_selector", ".trans-abstract, .trans-abstract > div.section")

        # Null:
        citations = ''
        search_keyword = ''
        source_impact_factor = ''

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

        # def get_id(self, element):
        #     """Return unique identifier for article ID."""
        #     return str(uuid.uuid4())

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
            """Gather article date publication, in YYYY-MM-DD format
            Args:
                element(:obj: `centaurminer.Element`): Page element to
                    gather body data from.
            Return:
                String representing date publication, in format YYYY-MM-DD.
            """
            try:
                date_str = str(self.get(element).split('Epub ')[1])
                try:
                    date_obj = datetime.datetime.strptime(date_str, '%b %d, %Y').date()
                except ValueError:
                    date_obj = datetime.datetime.strptime(date_str, '%B %d, %Y').date()
                return date_obj
            except (AttributeError, IndexError):
                element = mining.MetaData("citation_date")
                try:
                    return datetime.datetime.strptime(self.get(element), "%m/%Y").date()
                except Exception as e:
                    return None
            except:
                return None
            # try:
                # return str((self.get(element).split('Epub')[1]).date())
            # except (AttributeError, IndexError):
                # return None

        def get_organization_affiliated(self, element):
            """Returns a string with article authors organizations, separated by HTML-like elements"""
            orgs = [o.split('</sup>')[-1] for o in self.get(element, several=True)]
            return mining.TagList(orgs, "orgs")

        def get_references(self, element):
            """Returns a string with article references, separated by HTML-like elements"""
            reflist = self.get(element, several=True)
            refs = [r.replace('[ Links ]', '').strip('0123456789. ') for r in reflist]
            return refs

        def get_authors(self, element):
            """Returns a string with article authors from search engine, separated by HTML-like elements"""
            authors = map(self.__format_author, self.get(element, several=True))
            return mining.TagList(list(dict.fromkeys(authors)), "author")

        def get_keywords(self, element):
            """Gather article keywords from centaurminer.Element object.
            Args:
                element(:obj: `centaurminer.Element`): Page element to gather keywords from.
            Returns:
                String comprising keywords separated by HTML-like tags.
            """
            keys = self.__parse_keywords(self.get(element))
            if keys:
                return mining.TagList(keys, "keyword")
            return None

        def get_title_translated(self, element):
            """Returns a string with translated title/s"""
            return self.get(element, several=True)

        def get_abstract_translated(self, element):
            """Returns a string with translated abstract/s"""
            return self.get(element, several=True)

        def get_extra_link(self, element):
            """Returns a string with link to pdf/s"""
            return self.get(element, several=True)
