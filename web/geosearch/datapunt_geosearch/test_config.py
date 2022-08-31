import logging
from datapunt_geosearch.base_config import DATAPUNT_API_URL, DEFAULT_SEARCH_DATASETS, db_connection_string, get_db_settings, JWKS_TEST_KEY, JWKS, JWKS_SIGNING_ALGORITHMS, JWKS_URL, JW_KEYSET

# db entries are overridden
DSN_BAG = db_connection_string.format(**get_db_settings('bag_v11') | {'db': 'test_bag_v11'})
DSN_NAP = db_connection_string.format(**get_db_settings('nap') | {'db': 'test_nap'})
DSN_MILIEU = db_connection_string.format(**get_db_settings('milieuthemas') | {'db': 'test_milieuthemas'})
DSN_MONUMENTEN = db_connection_string.format(**get_db_settings('monumenten') | {'db': 'test_monumenten'})
DSN_VARIOUS_SMALL_DATASETS = db_connection_string.format(**get_db_settings('various_small_datasets') | {'db': 'test_various_small_datasets'})
DSN_DATASERVICES_DATASETS = db_connection_string.format(**get_db_settings('dataservices') | {'db': 'test_dataservices'})
TESTING = True
ENV = "test"

logging.debug('Database config:\n'
              'Bag: %s\n'
              'Nap: %s\n'
              'Milieu: %s\n'
              'Monumenten: %s\n',
              'Various Small Datasets: %s\n',
              'Dataservices: %s\n',
              DSN_BAG, DSN_NAP, DSN_MILIEU, DSN_MONUMENTEN, DSN_VARIOUS_SMALL_DATASETS, DSN_DATASERVICES_DATASETS)
