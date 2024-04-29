import logging

from datapunt_geosearch.base_config import db_connection_string, get_db_settings  # noqa: F401

DSN_DATASERVICES_DATASETS = db_connection_string.format(
    **get_db_settings("dataservices") | {"db": "test_dataservices"}
)
TESTING = True
ENV = "test"

logging.debug(
    "\n\nApp test Database config:\n\
        Dataservices: %s\n\n",
    DSN_DATASERVICES_DATASETS,
)

DATABASE_SET_ROLE = False
