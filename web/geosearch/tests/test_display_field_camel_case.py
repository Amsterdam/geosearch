import time
import unittest

from schematools.utils import to_snake_case

from datapunt_geosearch.registry import DatasetRegistry, registry


class TestDisplayFieldCamelCase(unittest.TestCase):
    
    def test_camelcase_to_snake_case(self):
        """ 
            Test if display field contains a camelCase based field name reference, 
            the content is translated to snake_case (result: matching the DB column name)
        """
        row = dict(
            schema="test",
            table_name="test_table",
            name="test_name",
            name_field="testDisplayFieldInCamelCase",
            geometry_type="POLYGON",
            geometry_field="geometry",
            id_field="id",
            dataset_name="test",
        )
        test_registry = DatasetRegistry()
        test_registry._datasets_initialized = time.time()
        # mimicing the logic with dataservices datasets (see registry.py)
        result = test_registry.init_dataset(row, "TestDataset", "DSN_TEST_DATASET", field_name_transformation=lambda field_id: to_snake_case(field_id))
        self.assertEqual(result.metadata["fields"][0], "test_display_field_in_camel_case as display")