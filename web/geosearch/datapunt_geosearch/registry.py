from collections import defaultdict
import logging
import psycopg2.extras
import time
from datapunt_geosearch.config import (
    DATAPUNT_API_URL,
    DSN_VARIOUS_SMALL_DATASETS
)
from datapunt_geosearch.db import dbconnection
from datapunt_geosearch.exceptions import DataSourceException

_logger = logging.getLogger(__name__)


class DatasetRegistry:
    """
    Dataset Registry.
    """

    INITIALIZE_DELAY = 600  # 10 minutes

    def __init__(self, delay=None):
        # Datasets is a dictionary of DSN => Datasets.
        self.datasets = defaultdict(list)
        self.providers = dict()
        self.static_dataset_names = []
        self._datasets_initialized = None
        if delay is not None:
            self.INITIALIZE_DELAY = delay

    def register_dataset(self, dsn_name, dataset_class):
        self.datasets[dsn_name].append(dataset_class)

        for key in dataset_class.metadata['datasets'].keys():
            self.providers[key] = dataset_class
            for item in dataset_class.metadata['datasets'][key].keys():
                if item in self.providers.keys():
                    _logger.warning("Provider for {} already defined {}".format(
                        item,
                        self.providers[item]
                    ))
                self.providers[item] = dataset_class

    def get_all_datasets(self):
        self.init_datasets()
        return self.providers

    def get_all_dataset_names(self):
        return self.get_all_datasets().keys()

    def get_by_name(self, name):
        return self.get_all_datasets().get(name)

    def filter_datasets(self, names):
        return set([dataset for name, dataset in self.get_all_datasets().items() if name in names])

    def init_dataset(self, row, class_name, dsn_name):
        from datapunt_geosearch.datasource import DataSourceBase
        if row['schema'] is None:
            row['schema'] = 'public'
        schema_table = row['schema'] + '.' + row['table_name']

        if row['geometry_type'].upper() == 'POLYGON':
            operator = 'contains'
        else:
            operator = 'within'
        name = row['name']
        name_field = row['name_field']
        geometry_field = row['geometry_field']
        id_field = row['id_field']

        dataset_class = type(class_name, (DataSourceBase,), {
            'metadata': {
                'geofield': geometry_field,
                'operator': operator,
                'datasets': {
                    'vsd': {
                        name: schema_table,
                    }
                },
                'fields': [
                    f"{name_field} as display",
                    f"cast('vsd/{name}' as varchar(30)) as type",
                    f"'{DATAPUNT_API_URL}vsd/{name}/' || {id_field} || '/'  as uri",
                    f"{geometry_field} as geometrie",
                    f"{id_field} as id",
                ],
            },
            'dsn_name': dsn_name
        })

        self.register_dataset(
            dsn_name=dsn_name,
            dataset_class=dataset_class
        )
        return dataset_class

    def init_datasets(self):
        if self._datasets_initialized is None or time.time() - self._datasets_initialized > self.INITIALIZE_DELAY:
            self.init_vsd_datasets()
            self._datasets_initialized = time.time()

    def init_vsd_datasets(self, dsn=None):
        if dsn is None:
            dsn = DSN_VARIOUS_SMALL_DATASETS
        try:
            dbconn = dbconnection(dsn)
        except psycopg2.Error as e:
            _logger.error('Error creating connection: %s' % e)
            raise DataSourceException('error connecting to datasource') from e

        sql = '''
select *
from cat_dataset
where enable_geosearch = true
        '''
        datasets = dict()
        for row in dbconn.fetch_dict(sql):
            # Fetch primary key field. We need to know what the id is
            if 'pk_field' in row:
                row['id_field'] = row.pop('pk_field')
            else:
                sql_pk = '''
select n data_type, db_column
from cataset_fields
where dat_id = %(ds_id)s and primary_key = true
                '''
                with dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur1:
                    cur1.execute(sql_pk, {'ds_id': row['id']})
                    pk_row = cur1.fetchone()
                    id_field = pk_row['db_column']

                    row['id_field'] = id_field

            datasets[row['name']] = self.init_dataset(
                row=row,
                class_name=row['name'].upper() + 'GenAPIDataSource',
                dsn_name='DSN_VARIOUS_SMALL_DATASETS')

        return datasets


registry = DatasetRegistry()
