from collections import defaultdict
import logging
import psycopg2.extras
from string_utils import slugify
import time
from datapunt_geosearch.config import (
    DATAPUNT_API_URL,
    DSN_VARIOUS_SMALL_DATASETS,
)
from datapunt_geosearch.db import dbconnection
from datapunt_geosearch.exceptions import DataSourceException

from schematools.utils import to_snake_case

_logger = logging.getLogger(__name__)


class DatasetRegistry:
    """
    Dataset Registry.
    """

    INITIALIZE_DELAY = 300  # 5 minutes

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

        for key in dataset_class.metadata["datasets"].keys():
            self.providers[key] = dataset_class
            for item in dataset_class.metadata["datasets"][key].keys():
                item_key = f"{key}/{item}"
                if (
                    item in self.providers.keys()
                    and self.providers[item] != dataset_class
                ):
                    _logger.debug(
                        "Provider for {} already defined {} and will be overwritten by {}.".format(
                            item, self.providers[item], dataset_class
                        )
                    )
                self.providers[item_key] = dataset_class

    def register_external_dataset(self, name, base_url, path, field_mapping=None):
        from datapunt_geosearch.datasource import ExternalDataSource
        class_name = "{}ExternalDataSource".format(name.upper())

        meta = {
            "base_url": base_url,
            "datasets": {
                name: {
                    name: path
                }
            }
        }
        if field_mapping is not None:
            meta["field_mapping"] = field_mapping

        dataset_class = type(
            class_name,
            (ExternalDataSource,),
            dict(metadata=meta)
        )

        self.register_dataset("EXT_{}".format(name.upper()), dataset_class)
        return dataset_class

    def get_all_datasets(self):
        self.init_datasets()
        return self.providers

    def get_all_dataset_names(self):
        return self.get_all_datasets().keys()

    def get_by_name(self, name):
        return self.get_all_datasets().get(name)

    def filter_datasets(self, names=None, scopes=None):
        return set(
            [
                dataset
                for name, dataset in self.get_all_datasets().items()
                if name in names and dataset.check_scopes(scopes=scopes)
            ]
        )

    def init_dataset(self, row, class_name, dsn_name,
                     base_url=None,
                     scopes=None,
                     field_name_transformation=None):
        """
        Initialize dataset class and register it in registry based on row data

        Args:
          row (dict): Dictionary with keys:
            - schema,
            - name,
            - name_field,
            - table_name,
            - geometry_field,
            - geometry_type,
            - id_field
            - dataset_name
          class_name (str): Name for the new class
          dsn_name: DSN name for namespacing
          scopes: Optional comma separated list of Authentication scopes for dataset.
          field_name_transformation: Optional function that will transform field names.

        Returns:
          DataSourceBase subclass for given dataset.
        """
        from datapunt_geosearch.datasource import DataSourceBase
        if field_name_transformation is None:
            field_name_transformation = lambda x: x

        if row.get("schema") is None:
            row["schema"] = "public"
        schema_table = row["schema"] + "." + row["table_name"]

        if row["geometry_type"] and \
           row["geometry_type"].upper() in ["POLYGON", "MULTIPOLYGON"]:
            operator = "contains"
        else:
            operator = "within"

        if not all([row["name"],
                    row["name_field"],
                    row["dataset_name"],
                    row["geometry_field"], row["id_field"]]):
            _logger.warn(f"Incorrect dataset: {class_name}")
            return None
        name = field_name_transformation(row["name"])
        name_field = field_name_transformation(row["name_field"])
        dataset_name = field_name_transformation(row["dataset_name"])
        geometry_field = field_name_transformation(row["geometry_field"])
        id_field = field_name_transformation(row["id_field"])

        base_url = base_url or DATAPUNT_API_URL

        dataset_class = type(
            class_name,
            (DataSourceBase,),
            {
                "metadata": {
                    "geofield": geometry_field,
                    "operator": operator,
                    "datasets": {dataset_name: {name: schema_table}},
                    "scopes": scopes or set(),
                    "fields": [
                        f"{name_field} as display",
                        f"cast('{dataset_name}/{name}' as varchar(50)) as type",
                        f"'{base_url}{dataset_name}/{name}/' || {id_field} || '/'  as uri",
                        f"{geometry_field} as geometrie",
                        f"{id_field} as id",
                    ],
                },
                "dsn_name": dsn_name,
            },
        )

        self.register_dataset(dsn_name=dsn_name, dataset_class=dataset_class)
        return dataset_class

    def init_datasets(self):
        if (
            self._datasets_initialized is None
            or time.time() - self._datasets_initialized > self.INITIALIZE_DELAY
        ):
            self.init_vsd_datasets()
            self.init_dataservices_datasets()
            self._datasets_initialized = time.time()

    def init_vsd_datasets(self, dsn=None):
        """
        Initialize datasets for all Various Small Datasets.
        Returns dict with datasets created.
        """
        if dsn is None:
            dsn = DSN_VARIOUS_SMALL_DATASETS
        try:
            dbconn = dbconnection(dsn)
        except psycopg2.Error as e:
            _logger.error("Error creating connection: %s" % e)
            raise DataSourceException("error connecting to datasource") from e

        sql = """
    SELECT
        name,
        name_field,
        schema,
        table_name,
        geometry_type,
        geometry_field,
        pk_field as id_field,
        'vsd' as dataset_name
    FROM cat_dataset
    WHERE enable_geosearch = true
        """
        datasets = dict()
        for row in dbconn.fetch_all(sql):
            dataset = self.init_dataset(
                row=row,
                class_name=row["name"].upper() + "GenAPIDataSource",
                dsn_name="DSN_VARIOUS_SMALL_DATASETS",
                base_url=f"{DATAPUNT_API_URL}",
            )
            if dataset is not None:
                datasets[row["name"]] = dataset

        return datasets

    def init_dataservices_datasets(self, dsn=None):
        if dsn is None:
            try:
                from datapunt_geosearch.config import DSN_DATASERVICES_DATASETS
            except ImportError:
                return
            else:
                dsn = DSN_DATASERVICES_DATASETS
        try:
            dbconn = dbconnection(dsn)
        except psycopg2.Error as e:
            _logger.error("Error creating connection: %s" % e)
            raise DataSourceException("error connecting to datasource") from e

        sql = """
    SELECT
        dt.name,
        dt.display_field as name_field,
        dt.db_table as table_name,
        dt.geometry_field_type as geometry_type,
        dt.geometry_field,
        'id' as id_field,
        d.name as dataset_name,
        d.auth as dataset_authorization,
        dt.auth as datasettable_authorization
    FROM datasets_datasettable dt
    LEFT JOIN datasets_dataset d
      ON dt.dataset_id = d.id
    WHERE d.enable_api = true AND dt.enable_geosearch = true
        """
        datasets = dict()
        for row in dbconn.fetch_all(sql):
            scopes = set()
            if row["dataset_authorization"]:
                scopes = set(row["dataset_authorization"].split(","))
            if row["datasettable_authorization"]:
                scopes.update(set(
                    row["datasettable_authorization"].split(",")
                ))
            dataset = self.init_dataset(
                row=row,
                class_name=row["dataset_name"]
                + row["name"]
                + "DataservicesDataSource",
                dsn_name="DSN_DATASERVICES_DATASETS",
                base_url=f"{DATAPUNT_API_URL}v1/",
                scopes=scopes,
                field_name_transformation=lambda field_id: to_snake_case(field_id)
            )
            if dataset is not None:
                key = f"{row['dataset_name']}/{row['name']}"
                datasets[key] = dataset
        return datasets


registry = DatasetRegistry()
