import unittest

from datapunt_geosearch import config
from datapunt_geosearch.datasource import DataSourceBase
from datapunt_geosearch.registry import DatasetRegistry

class TestFieldType50Karakters(unittest.TestCase):
    
    def test_field_type_50_karakters(self):
        """ Test if output field 'type' => product of '[dataset_name]/[name]' can handle 50 characters """

        # setup test row with name and dataset_name combined (plus the forward slash) is 50 characters
        # table_name could be anything, fietsplaatjes was choosen as mediator
        test_row = dict(
            schema="public",
            table_name="fietspaaltjes_fietspaaltjes",
            name="0123456789-0123456789-123",
            name_field="id",
            geometry_type="POINT",
            geometry_field="geometry",
            id_field="id",
            operator="contains",
            dataset_name="0123456789-0123456789-12",
        )          

        # setup context data
        registry = DatasetRegistry()
        context_data = registry.init_dataset(row=test_row, class_name="TestDataset", dsn_name=config.DSN_DATASERVICES_DATASETS)
        
        # make connection and set vars
        dataset = DataSourceBase(connection=None, dsn=context_data.dsn_name)
        dataset.meta = context_data.metadata
        dataset.x = 123207
        dataset.y = 486624
        dataset.radius = 50
        
        query_result = dataset.execute_queries()            
        
        self.assertEqual(str(query_result[0]['properties']['type']), "0123456789-0123456789-12/0123456789-0123456789-123")
