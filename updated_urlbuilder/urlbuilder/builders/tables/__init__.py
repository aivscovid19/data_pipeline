from os import environ
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

class BQTable:
    table_id = None
    schema = None
    def __init__(self):
        self._table = None
        self._client = None

    def GetOrCreate(self, project_id = None, dataset_id = None, table_name = None):
        '''
        Gets a table from bigquery, or creates it if necessary. Returns a reference to that table.

        Updates self.table_id if any arguments are supplied.
        '''
        #table_id = environ.get("TABLE_ID").split(".")
        table_id = self.table_id.split(".")
        
        # Overwrite from arguments
        if project_id is not None:
            table_id[0] = project_id
        else:
            project_id = table_id[0]
        if dataset_id is not None:
            table_id[1] = dataset_id
        if table_name is not None:
            table_id[2] = table_name

        self.table_id = ".".join(table_id)

        _table = bigquery.Table(self.table_id, schema = self.schema)
        self._client = bigquery.Client(project_id)

        try:
            self._table = self._client.get_table(_table)
        except NotFound as e:
            print(f"Creating table {table_id}.", flush=True)
            self._table = self._client.create_table(_table)

        return self

    def Query(self, query):
        '''
        Queries the table using the given query, returning a list-of-dicts representation of the data.
        '''
        #client = bigquery.Client(self.table_id.split(".")[0])
        query_job = self._client.query(query)
        rows = query_job.result()
        json_rows = [ dict(row) for row in rows ]
        #json_rows = []
        #for row in rows:
        #    row = dict(row)
        #    row.pop('rn')  # Don't include the row number entry
        #    json_rows.append(row)
        return json_rows

    def insert_row(self, row):
        return self._client.insert_rows(
            table = self._table,
            rows = [row]
        )

    def insert_rows(self, rows):
        return self._client.insert_rows(
            table = self._table,
            rows = rows
        )

class StatusTable(BQTable):
    table_id = environ.get("STATUS_TABLE_ID")
    schema = [
        bigquery.SchemaField("article_url", "STRING",   mode = "REQUIRED"),
        bigquery.SchemaField("catalog_url", "STRING",   mode = "REQUIRED"),
        bigquery.SchemaField("is_pdf",      "INTEGER",  mode = "REQUIRED"),
        bigquery.SchemaField("language",    "STRING"                     ),
        bigquery.SchemaField("status",      "STRING",   mode = "REQUIRED"),
        bigquery.SchemaField("timestamp",   "DATETIME", mode = "REQUIRED"),
        bigquery.SchemaField("worker_id",   "STRING"                     ),
        bigquery.SchemaField("meta_info",   "STRING"                     )
    ]

    def GetNewURLs(self):
        QUERY = """
            SELECT """ + ",".join(col.name for col in self.schema) + """
                FROM (
                    SELECT *, ROW_NUMBER() OVER
                    (PARTITION BY article_url ORDER BY timestamp DESC) AS rn
                    FROM `""" + self.table_id + """`
                    )
            WHERE rn = 1 AND status='Not Mined' AND is_pdf = 0
            ORDER BY timestamp ASC
            LIMIT 100000;
        """
        return self.Query(QUERY)


class DataTable(BQTable):
    table_id = environ.get("DATA_TABLE_ID")
    schema = [
        bigquery.SchemaField("abstract",         "STRING",   mode = "REQUIRED"),
        bigquery.SchemaField("title",            "STRING",   mode = "REQUIRED"),
        bigquery.SchemaField("authors",          "STRING",   mode = "REQUIRED"),
        bigquery.SchemaField("language",         "STRING",   mode = "REQUIRED"),
        bigquery.SchemaField("doi",              "STRING"                     ),
        bigquery.SchemaField("acquisition_date", "DATETIME", mode = "REQUIRED"),
        bigquery.SchemaField("publication_date", "DATETIME"                   ),
        bigquery.SchemaField("link",             "STRING",   mode = "REQUIRED"),
        bigquery.SchemaField("source",           "STRING",   mode = "REQUIRED"),
        bigquery.SchemaField("meta_info",        "STRING"                     ),
        bigquery.SchemaField("body",             "STRING"                     )
    ]
