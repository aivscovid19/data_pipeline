"""
Scielo miner by Adrian R.
Edited by Gulnoza Kh. on 2020-12-17
Edited by Simon Ewing on 2021-02-18
"""

import centaurminer as mining
import datetime
import re
import numpy as np
import html


class ScieloMiner:
    """
    Miners for https://scielo.org
    """
    abstract_keywords = {
            "abstract": "english",
            "resumo": "portuguese",  # abstract
            "resumen": "spanish"  # abstract
        }


    ack_keywords = {
            "agradecimentos": "portuguese",  # acknowledgements
            "referências": "portuguese",  # references
            "references": "english",
            "referências bibliográficas": "portuguese"  # bibliographical references
        }

    key_strings = [
        "keywords",
        "key words",
        "palavras-chave",
        "palavras chave",
        "index terms",
        "descritores",
        "unitermos"
    ]


    class ScieloLocationsBase(mining.PageLocations):
        date_publication = mining.Element("css_selector", ".content > h3")
        language = mining.MetaData("citation_language")
        organization_affiliated = mining.MetaData("citation_author_institution")
        source = mining.MetaData("citation_journal_title")
        title = mining.Complex()

        license = "https://scielo.org/en/about-scielo/open-access-statement/"


    class ScieloEngineBase(mining.MiningEngine):
        def get_date_publication(self, element):
            """
            Gather article date publication - look first for a specific element, then
            look at metadata if it's not found.

            (Some metadata is corrupted, hence needing to look at a page element)
            """
            date_elem = self.get(element).split('Epub ')
            if len(date_elem) > 1:
                date_str = str(date_elem[1])
                try:
                    date_obj = datetime.datetime.strptime(date_str, '%b %d, %Y').date()
                except ValueError:
                    date_obj = datetime.datetime.strptime(date_str, '%B %d, %Y').date()
                return date_obj
            else:
                element = mining.MetaData("citation_date")
                date = self.get(element)
                try:
                    if date.startswith("00/"):
                        self.results['publication_date_missing_month'] = True
                        self.results['publication_date_missing_day'] = True
                        return datetime.datetime.strptime(date, "00/%Y").date()
                    else:
                        self.results['publication_date_missing_day'] = True
                        return datetime.datetime.strptime(date, "%m/%Y").date()
                except ValueError as e:
                    return None

        def get_organization_affiliated(self, element):
            orgs = self.get(element, several=True)
            return mining.TagList(orgs, "org")

        def get_title(self, element):
            element = mining.MetaData("citation_title")
            title = self.get(element)
            if title is not None:
                return title

            element = mining.Element("css_selector", "p.title")
            title = self.get(element)
            return title


    class ScieloLocationsStructured(ScieloLocationsBase):
        '''
        Locations for the simplest format on scielo: content has class names and id's, and is overall well-structured.

        In all tests, the language and title match
        '''
        abstract = mining.Element("css_selector", ".trans-abstract > p")
        category = mining.Element("xpath", "//p[@class='categoria']")
        body = mining.Element("id", "article-body")
        references = mining.Element("css_selector", "#article-back > div > p.ref")

        # addition to meta-info:
        title_translated = mining.Element("css_selector", "p.trans-title")


    class ScieloEngineStructured(ScieloEngineBase):
        '''
        Throughout the mining, the following extra fields are created as results (to be passed into meta-info):
         - keywords
         - other_abstracts
         - abstract_lang
        '''
        def get_abstract(self, element):
            '''
            Each abstract comes in a group of 3 p-tags (somewhat brittle):
              1) section header (e.g. ABSTRACT)
              2) actual abstract
              3) keywords (';' delimited)
            '''
            abstracts = self.get(element, several = True)
            if not abstracts:
                return None

            abstracts = np.asarray(abstracts).reshape((-1,3))
            abstract = None
            for title, paragraph, keywords in abstracts:
                # Save keywords (after the beginning "Key words:" string)
                keywords = keywords.split(':')[1].split(';')
                if "keywords" not in self.results:
                    self.results['keywords'] = []
                self.results['keywords'].extend([ key.strip(' .') for key in keywords])
                if abstract is None:
                    abstract = paragraph.strip()
                    for phrase, lang in ScieloMiner.abstract_keywords.items():
                        if title.lower() == phrase:
                            self.results['abstract_lang'] = lang
                            break
                else:
                    if "other_abstracts" not in self.results:
                        self.results['other_abstracts'] = []
                    for phrase, lang in ScieloMiner.abstract_keywords.items():
                        if title.strip('.:').lower() == phrase:
                            self.results['other_abstracts'] = {lang: paragraph}
                            break
            return abstract

        def get_references(self, element):
            references = self.get(element, several=True)
            references = [html.unescape(ref) for ref in references]
            references = [ref.strip('01243456789. []') for ref in references]
            references = [ref.replace(' [ Links', '') for ref in references]
            return mining.TagList(references, "reference")

        def get_organization_affiliated(self, element):
            orgs = self.get(element, several=True)

            # All orgs are doubled in this format
            orgs = orgs[::2]
            return mining.TagList(orgs, "org")

        def get_title_translated(self, element):
            titles = self.get(element, several=True)
            return mining.TagList(titles, "title")


    class ScieloLocationsFlat(ScieloLocationsBase):
        abstract = mining.Element("css_selector", ".index\,pt > p, .index\,en > p, .index\,es > p")
        body = mining.Element("css_selector", ".index\,pt > p, .index\,en > p, .index\,es > p")
        category = mining.Element("css_selector", ".index\,pt > p, .index\,en > p, .index\,es > p")

        references = mining.Complex()

        # addition to meta-info:
        title_translated = mining.Complex()

    class ScieloEngineFlat(ScieloEngineBase):
        def get_abstract(self, element):
            '''
            Get the keywords and translated abstracts at the same time
            '''
            paragraphs = self.get(element, several=True)

            abstract = None
            self.results['keywords'] = []
            for idx, text in enumerate(paragraphs):
                for abs_keyword, language in ScieloMiner.abstract_keywords.items():
                    if text.lower() == abs_keyword:
                        # extract the next paragraph as an abstract
                        if idx + 1 >= len(paragraphs):
                            continue
                        elif abstract is None:
                            abstract = paragraphs[idx + 1]
                            self.results['abstract_lang'] = language
                        else:
                            if 'other_abstracts' not in self.results:
                                self.results['other_abstracts'] = []
                            self.results['other_abstracts'].append({language: paragraphs[idx + 1]})
                        
                        # Check the next (idx+2) paragraph for keywords
                        if idx + 2 >= len(paragraphs):
                            continue
                        keywords = paragraphs[idx + 2]
                        for keyword in ScieloMiner.key_strings:
                            if keyword in keywords.lower():
                                # Check if keywords text has some translation for "keywords"
                                keywords = re.split(";|:|,", re.sub("^[^:]*:", "", keywords))
                                self.results['keywords'].extend([ key.strip(' .') for key in keywords])
                                break
                        break
            if not self.results['keywords']:
                del self.results['keywords']

            return abstract

        def get_body(self, element):
            body = self.get(element, several=True)

            cleaned_paragraphs = []
            abstract_index = 0
            ack_index = -1
            # Find which paragraphs transition from abstract -> body -> references
            for idx, p in enumerate(body):
                if p.strip(":.").lower() in ScieloMiner.abstract_keywords.keys():
                    abstract_index = idx
                if p.strip(":.").lower() in ScieloMiner.ack_keywords.keys():
                    ack_index = idx
            # Clean up and join the paragraphs
            for p in body[abstract_index + 2: ack_index]:
                skip_keywords = False
                for keyword_phrase in ScieloMiner.key_strings:
                    if p.lower().startswith(keyword_phrase):
                        skip_keywords = True
                        break
                if skip_keywords:
                    continue

                p = html.unescape(p).strip()
                if p:
                    cleaned_paragraphs.append(p)
            if cleaned_paragraphs == []:
                return None
            return "\n".join(cleaned_paragraphs)


        def get_references(self, element):
            '''
            Get references using the handy comments added by Scielo. But then remove all
            of the HTML fluff to get just the text we want.
            '''
            refs = re.findall(r"<!-- ref -->(.*?)<!-- end-ref -->", self.wd.page_source)
            # -- Remove "Links" hypertext and the enclosing a-tag
            refs = [re.sub(r"<a[^>]*>Links</a>", "", ref) for ref in refs]
            
            #  -- Remove any remaining HTML tags
            refs = [re.sub(r"</?[^>]*>", "", ref) for ref in refs]

            # -- Replace HTML entities with the most reasonable character
            refs = [ref.replace("&nbsp;","") for ref in refs]
            refs = [ref.replace("&amp;","&") for ref in refs]

            # -- Final cleaning pass to remove extra marks
            refs = [ref.replace("[]","") for ref in refs]  # Leftover from the [Links] text at the end
            refs = [re.sub(r" +", " ", ref) for ref in refs]
            refs = [ref.lstrip("0123456789.[] ") for ref in refs]  # Remove numbering
            refs = [ref.strip() for ref in refs]
            return mining.TagList(refs, "reference")


        def get_title_translated(self, element):
            '''
            All titles have the attribute size >= 3. However, subsection headers do as well.
            Use the abstract keywords to search p-tags at the beginning of the document for titles.
            '''
            element = mining.Element("xpath", "//*[@size>=3]")
            headers = self.get(element, several=True)
            paras = self.get(self.site.body, several=True)

            done_searching = False
            trans_titles = []
            for para in paras:
                cleaned_para = para.strip(":;. ").lower()
                for phrase in ScieloMiner.abstract_keywords.keys():
                    if cleaned_para.startswith(phrase):
                        done_searching = True
                        break
                if done_searching:
                    break
                
                #  Check against the headers and add if it is
                for header in headers:
                    if para == header:
                        trans_titles.append(header)
                        break

            return trans_titles if trans_titles else None

#    class ScieloLocations(mining.PageLocations):
#        """Locations on the page to be gathered by Selenium webdriver
#
#        The locations may be declared here as static variables of any type, to be retrieved
#        as keys on the centaurminer.MiningEngine.results dictionary. Some examples of data that
#        can be declared here:
#
#        centaurminer.Metadata: Selenium retrieved elements from a page metadata
#        centaurminer.Element: Selenium retrived elements from a page body.
#        string: Strings declared here won't change, independently of the page searched.
#        """
#        # Most of these complex elements come from the fact that they don't have a coherent format
#        abstract = mining.Complex()  # Further instructions in the engine
#        body = mining.Element("css_selector", "#article-body, .index\,pt > p, .index\,en > p, .index\,es > p")
#        category = mining.Element("xpath", "//p[@class='categoria']")
#        date_publication = mining.Element("xpath", "//div[@class='content']/h3")
#        keywords = mining.Element("css_selector", ".trans-abstract > p:last-of-type")
#        language = mining.MetaData("citation_language")
#        license = "https://scielo.org/en/about-scielo/open-access-statement/"
#        organization_affiliated = mining.Element("css_selector", "p.aff").get_attribute('innerHTML')
#        references = mining.Complex()  # mining.Element("css_selector", "p.ref")
#        source = mining.MetaData("citation_journal_title")
#        title = mining.Complex()
#        #title = mining.Element("css_selector", "p.title")
#
#        # addition to meta-info:
#        title_translated = mining.Complex() #"css_selector", "p.trans-title")
#        abstract_translated = mining.Element("css_selector", ".trans-abstract, .trans-abstract > div.section")
#
#        # Null:
#        #citations = ''
#        #search_keyword = ''
#        #source_impact_factor = ''
#
#    class ScieloEngine(mining.MiningEngine):
#        """Mining Engine to get data from elements declared on centaurminer.PageLocations
#
#        Here it's possible to process elements retrieved from centaurminer.PageLocations
#        before gathering the results as a dictionary. To modify a specific element, declare
#        a new method in the form get_<key>.
#
#        Example:
#            def get_authors(self, element):
#                return TagList(self.get(element, several=True))
#        """
#        #########################
#        ### Utilities Methods ###
#        #########################
#
#        @staticmethod
#        def __format_author(author):
#            """Formats a single author entry in full name format."""
#            author = ' '.join(author.split(",")[::-1])
#            return author.title().strip()
#
#        @staticmethod
#        def __parse_keywords(keys):
#            """Extract keywords from HTML element"""
#            key_strings = [
#                "keywords",
#                "key words",
#                "palavras-chave",
#                "palavras chave",
#                "index terms",
#                "descritores"
#            ]
#            if not keys:
#                return None
#            for i in key_strings:
#                if keys.lower().startswith(i):
#                    keys = keys[len(i):]
#            return keys.replace(':', ' ').replace(';',',').split(',')
#
#        ##################################
#        ### Element Processing Methods ###
#        ##################################
#
#        # def get_id(self, element):
#        #     """Return unique identifier for article ID."""
#        #     return str(uuid.uuid4())
#
#        def get_abstract(self, element):
#            """
#            There are several abstract formats on scielo that we need to distinguish:
#            - structured: Abstract in several languages, found in the ".trans-abstract" div.
#            - flat: No encapsulating divs between the abstract and body - separate using keywords for introduction.
#            - No abstract: Use the first paragraph of the body.
#            """
#            # structured format - there can be multiple abstracts on the page
#            element = mining.Element("css_selector", ".trans-abstract")
#            # We can't use self.get, since we need to preserve the actual element first (for subsearching)
#            abstracts = self.wd.find_elements(element.method, element.selector)
#            abstract_text = []
#            for abstract in abstracts:
#                paragraphs = abstract.find_elements_by_css_selector("div.section")
#                abstract_text.append("\n".join([para.text for para in paragraphs]))
#            if len(abstract_text) >= 2:
#                self.results['other_abstracts'] = abstract_text[1:]
#            if abstract_text != []:
#                return abstract_text[0]
#
#            # flat format - get paragraphs after keywords resembling "ABSTRACT"
#            print("Look for flat format")
#            abstract = None
#
#            element = mining.Element("css_selector", ".index\,pt > p, .index\,en > p, .index\,es > p")
#            paragraphs = self.get(element, several=True)
#            print("Paragraphs:", len(paragraphs))
#            for idx, text in enumerate(paragraphs):
#                #print('"' + text + '"')
#                for keyword, language in ScieloMiner.abstract_keywords.items():
#                    if text.lower() == keyword:
#                        print("Matched", text)
#                        if idx + 1 >= len(paragraphs):
#                            return None  # We're done, just return
#                        elif abstract is None:
#                            abstract = paragraphs[idx + 1]
#                            self.results['abstract_lang'] = language
#                        else:
#                            if 'other_abstracts' not in self.results:
#                                self.results['other_abstracts'] = []
#                            self.results['other_abstracts'].append({language: paragraphs[idx + 1]})
#
#            return abstract
#
#            def get_body(self, element):
#                """Gather body text from article URL
#                Note:
#                    If body is retrieved from #article-body selector, it's safe
#                    to assume that it'll be pretty formatted. Otherwise, it's
#                required to process <p> tags to retrieve body information.
#            Aegs:
#                element(:obj: `centaurminer.Element`): Page element to gather body data from.
#            "eturn:
#                String comprising whole body data
#            """
#            body = self.get(element, several=True)
#            # Return if get from #article-body selector
#            if len(body) == 1:
#                return body[0]
#            cleaned_paragraphs = []
#            abstract_index = 0
#            ack_index = -1
#            for idx, p in enumerate(body):
#                if p.lower() in ScieloMiner.abstract_keywords.keys():
#                #if p.lower() in ["resumo", "abstract", "resumen"]:
#                    abstract_index = idx
#                if p.lower() in ScieloMiner.ack_keywords.keys():
#                    ack_index = idx
#            # Clean up and join the paragraphs
#            for p in body[abstract_index + 1: ack_index]:
#                p = p.replace('&nbsp;',' ').strip()
#                just_whitespace = all(char == " " for char in p)
#                if not just_whitespace:
#                    cleaned_paragraphs.append(p)
#            if cleaned_paragraphs == []:
#                return None
#            return "\n".join(cleaned_paragraphs)
#
#        def get_date_publication(self, element):
#            """Gather article date publication, in YYYY-MM-DD format
#            Args:
#                element(:obj: `centaurminer.Element`): Page element to
#                    gather body data from.
#            Return:
#                String representing date publication, in format YYYY-MM-DD.
#            """
#            try:
#                date_str = str(self.get(element).split('Epub ')[1])
#                try:
#                    date_obj = datetime.datetime.strptime(date_str, '%b %d, %Y').date()
#                except ValueError:
#                    date_obj = datetime.datetime.strptime(date_str, '%B %d, %Y').date()
#                return date_obj
#            except (AttributeError, IndexError):
#                element = mining.MetaData("citation_date")
#                try:
#                    return datetime.datetime.strptime(self.get(element), "%m/%Y").date()
#                except Exception as e:
#                    return None
#            except:
#                return None
#            # try:
#                # return str((self.get(element).split('Epub')[1]).date())
#            # except (AttributeError, IndexError):
#                # return None
#
#        def get_organization_affiliated(self, element):
#            """Returns a string with article authors organizations, separated by HTML-like elements"""
#            orgs = [o.split('</sup>')[-1] for o in self.get(element, several=True)]
#            return mining.TagList(orgs, "orgs")
#
#        def get_references(self, element):
#            """
#            Look for a p.ref tag first. If these don't exist, use the html comments.
#            Returns a string with article references, separated by HTML-like elements
#            """
#            element = mining.Element("css_selector", "p.ref")
#            reflist = self.get(element, several=True)
#            if reflist != []:
#                refs = [r.replace('[ Links ]', '').strip('0123456789. ') for r in reflist]
#                return mining.TagList(refs, "reference")
#
#            refs = re.findall(r"<!-- ref -->(.*?)<!-- end-ref -->", self.wd.page_source)
#            # Remove all the bits and bobs that are in the html that we don't want
#            refs = [re.sub(r"<p>", "", ref) for ref in refs]
#            refs = [re.sub(r"<font[^>]*>", "", ref) for ref in refs]
#            refs = [re.sub(r"<a[^>]*>Links</a>", "", ref) for ref in refs]
#            refs = [re.sub(r"\[&nbsp;&nbsp;\]", "", ref) for ref in refs]
#            refs = [re.sub(r"&nbsp;", "", ref) for ref in refs]
#            refs = [re.sub(r" +", " ", ref) for ref in refs]
#            refs = [ref.strip() for ref in refs]
#            return mining.TagList(refs, "reference")
#
#        def get_authors(self, element):
#            """Returns a string with article authors from search engine, separated by HTML-like elements"""
#            authors = map(self.__format_author, self.get(element, several=True))
#            return mining.TagList(list(dict.fromkeys(authors)), "author")
#
#        def get_keywords(self, element):
#            """Gather article keywords from centaurminer.Element object.
#            Args:
#                element(:obj: `centaurminer.Element`): Page element to gather keywords from.
#            Returns:
#                String comprising keywords separated by HTML-like tags.
#            """
#            keys = self.__parse_keywords(self.get(element))
#            if keys:
#                return mining.TagList(keys, "keyword")
#            return None
#
#        def get_title(self, element):
#            '''
#            '''
#            element = mining.MetaData("citation_title")
#            title = self.get(element)
#            if title is not None:
#                return title
#
#            element = mining.Element("css_selector", "p.title")
#            title = self.get(element)
#            return title
#
#        def get_title_translated(self, element):
#            """Returns a string with translated title/s"""
#            element = mining.Element("css_selector", "p.trans-title")
#            trans = self.get(element, several=True)
#            if trans == []:
#                trans = None
#            return trans
#            #trans = self.get(element)
#            #if trans is not None:
#            #    return trans
#
#            #element = mining.Element("css_selector", "p:nth-of-type(5) > font > b")
#            #trans = self.get(element)
#            #return trans
#
#        def get_abstract_translated(self, element):
#            """Returns a string with translated abstract/s"""
#            trans = self.get(element, several=True)
#            if trans == []:
#                trans = None
#            return trans
#            #return self.get(element, several=True)
#
#        def get_extra_link(self, element):
#            """Returns a string with link to pdf/s"""
#            link = self.get(element, several=True)
#            if link == []:
#                link = None
#            return link
#            #return self.get(element, several=True)

if __name__ == "__main__":
    # Scrape a site given as a command line arg
    from sys import argv
    assert len(argv) == 2, "Must include a URL"

    

    miner = ScieloMiner.ScieloEngine(ScieloMiner.ScieloLocations)
    miner.gather(argv[1])
    [ print(f"{key}: {value}") for key, value in miner.results.items() ]

