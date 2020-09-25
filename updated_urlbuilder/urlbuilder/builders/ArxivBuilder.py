from datetime import datetime
import centaurminer as mining
from .tables import StatusTable

class ArxivSearchLocations(mining.PageLocations):
    """
    HTML locations on the earch page to be gathered by centaurminer
    """
    link_elem = mining.Element('css_selector', '.list-identifier > a:first-of-type').get_attribute('href')
    #link_elem = mining.Element('css_selector', '.list-identifier > a:first-of-type').get_attribute('href')

class URLBuilder:
    def __init__(self, miner = None):
        if miner is None:
            miner = mining.MiningEngine(ArxivSearchLocations)

        self.miner = miner

    def collect(self, keywords, limit=100, delay_time=1):
        print(keywords, flush=True)
        keywords_url = "tEmP+AND+tEmP".join(keywords).split("tEmP")  # add in "AND" between each element
        print(keywords_url, flush=True)
        keywords_url = keywords_url[1:] + ["+" + keywords_url[0]]  # Put the first keyword at the end
        print(keywords_url, flush=True)
        keyword_string = "".join(keywords_url)
        print(keyword_string, flush=True)

        base_url = "http://export.arxiv.org/find/all/1/all:" + keyword_string
        
        page_num = 0
        url = base_url + f"?skip={25*page_num}&show=25"
        self.miner.wd.get(url)
        elems = self.miner.get(self.miner.site.link_elem, several=True)
        print("url:", url, flush=True)
        print("elems:", elems, flush=True)

        statusTable = StatusTable().GetOrCreate(project_id = self.project_id, dataset_id = self.dataset_id, table_name = self.table_id)
        total_inserted = 0
        while len(elems) != 0:
            # Send elems to bigquery
            for elem in elems:
                status = {
                    'article_url': elem,
                    'catalog_url': url,
                    'is_pdf': 0,
                    'language': 'en',
                    'status': "Not Mined",
                    'timestamp': datetime.utcnow(),
                    'worker_id': None,
                    'meta_info': '{"search_terms": [' + ",".join(keywords) + ']}'
                }
                statusTable.insert_row(status)
                print("Inserting to table:", status)
                total_inserted += 1
                if total_inserted == limit:
                    break

            # Break out of outer (search page) loop if limit is reached
            if total_inserted == limit:
                break

            page_num += 1
            url = base_url + f"?skip={25*page_num}&show=25"
            elems = self.miner.get(self.miner.site.link_elem, several=True)

    @classmethod
    def connect_to_gbq(cls, credentials, project_id, url_table_id, schema=None):
        """ Establish a connection with Google BigQuery
        Args:
            credentials (:obj: `google.auth.credentials.Credentials`):
                Google Authentication credentials object, required to
                authorize the data workflow between this class and the
                database. Can be declared from service or user account.
            project_id (string): Google Cloud project ID.
            table_id (string): Table information to read and write data on.
                Must be specified as `<dataset_name>.<table_name>`.
            schema (`list` of `dict`: optional): Optional databse schema to
                input while working with `pandas_gbq` module. If `None`, the
                schema will be inferred from `pandas.DataFrame` object.
        Example:
            URLBuilder.connect_to_gbq(google-credentials, 'MyProject',
              'my_dataset.my_table', [{'name': 'url', 'type': 'STRING'}]).
        Auth_docs:
            Reference for Google BigQuery Authentication, on this context:
            'https://pandas-gbq.readthedocs.io/en/latest/howto/authentication.html'
        """
        cls.credentials = credentials
        cls.project_id = project_id
        cls.table_id = url_table_id
        cls.schema = schema

        # Gather pieces to identify a gbq table
        cls.project_id = project_id
        cls.dataset_id = url_table_id.split(".")[0]
        cls.table_id = url_table_id.split(".")[1]
        StatusTable.table_id = project_id + "." + url_table_id

