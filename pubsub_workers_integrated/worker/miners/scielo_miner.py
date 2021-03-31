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
import html2text


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

        def _clean_refs(self, refslist):
            h = html2text.HTML2Text()
            h.body_width = 0
            h.ignore_links = True

            refslist = [h.handle(ref) for ref in refslist]  # Remove html bits
            # Remove numbering that looks like 01\. or [01]
            refslist = [re.sub(r"^(\[[0-9]*\])|([0-9]*\\.)", "", ref) for ref in refslist]
            refslist = [re.sub(r" +", " ", ref) for ref in refslist]  # Limit duplicate spaces
            refslist = [ref.replace("[ Links ]", "") for ref in refslist]  # Remove irrelevant links text
            refslist = [ref.strip() for ref in refslist]  # final pass
            return refslist


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

            if len(abstracts) % 3 != 0:
                return None

            abstracts = np.asarray(abstracts).reshape((-1,3))
            abstract = None
            for title, paragraph, keywords in abstracts:
                # Save keywords (after the beginning "Key words:" string)
                if "keywords" not in self.results:
                    self.results['keywords'] = []
                for keyword in ScieloMiner.key_strings:
                    if keyword.lower().startswith(keyword):
                        # Remove the keyword string and maybe a following punctuation mark and space
                        keywords = re.sub(f"{keyword.lower()}[:;,.]? ?", "", keywords.lower())
                        keywords = re.split(";|:|,", keywords)
                        self.results['keywords'].extend([ key.strip(' .') for key in keywords])
                        break
                #keywords = keywords.split(':')[1].split(';')
                #self.results['keywords'].extend([ key.strip(' .') for key in keywords])
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
            references = self._clean_refs(references)
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
                            if keyword.lower().startswith(keyword):
                                # Remove the keyword string and maybe a following punctuation mark and space
                                keywords = re.sub(f"{keyword.lower()}[:;,.]? ?", "", keywords.lower())
                                keywords = re.split(";|:|,", keywords)
                                self.results['keywords'].extend([ key.strip(' .') for key in keywords])
                                break
                            #if keyword in keywords.lower():
                            #    # Check if keywords text has some translation for "keywords"
                            #    keywords = re.split(";|:|,", re.sub("^[^:]*:", "", keywords))
                            #    self.results['keywords'].extend([ key.strip(' .') for key in keywords])
                            #    break
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
            refs = self._clean_refs(refs)
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


if __name__ == "__main__":
    # Scrape a site given as a command line arg
    from sys import argv
    assert len(argv) == 2, "Must include a URL"

    

    miner = ScieloMiner.ScieloEngine(ScieloMiner.ScieloLocations)
    miner.gather(argv[1])
    [ print(f"{key}: {value}") for key, value in miner.results.items() ]

