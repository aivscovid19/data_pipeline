import uuid
from google.oauth2 import service_account
from site_worker_integrated import SiteWorkerIntegrated
from job_dispatcher import JobDispatcher

credentials = service_account.Credentials.from_service_account_file('credentials/key.json',)
project_id = 'for-gulnoza'
driver_path = '/usr/lib/chromium-browser/chromedriver'

worker_id = uuid.uuid1()
limit = 100

'''
# Test IbmcRuSiteWorker

urls_table = 'pbmc_v2.url_builder_med'
article_table = 'pbmc_v2.articles_med_10_17'
'''

'''
# Test ArxivSiteWorker

urls_table = 'arxiv_test.url_builder_virus'
article_table = 'arxiv_test.articles_10_18'
'''

'''
# Test BiorxivSiteWorker

urls_table = 'biorxiv_test.url_builder_virus'
article_table = 'biorxiv_test.articles_10_18'
'''

'''
# Test MedrxivSiteWorker

urls_table = 'medrxiv_test.url_builder_virus'
article_table = 'medrxiv_test.articles_10_17'
'''

'''
# Test PreprintsSiteWorker

urls_table = 'preprints_urlbuilder.test'
article_table = 'preprints_urlbuilder.articles_10_26'
'''

# Test ScieloSiteWorker

urls_table = 'scielo_urlbuilder.scielo_200k'
article_table = 'scielo_urlbuilder.articles_10_26'

urls_df = JobDispatcher(credentials, project_id, urls_table).register_job(worker_id, limit)

articles = SiteWorkerIntegrated()
articles.init(credentials, project_id, urls_table, article_table, driver_path=driver_path)
articles.send_request(urls_df, limit)

