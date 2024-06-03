import logging

from datapunt_geosearch.base_config import (  # noqa, this is imported from config.py and essential; noqa: F401
    DATABASE_SET_ROLE,
    DATAPUNT_API_URL,
    JW_KEYSET,
    JWKS,
    db_connection_string,
    get_db_settings,
)

dataservices_settings = get_db_settings("dataservices")
DSN_DATASERVICES_DATASETS = db_connection_string.format(
    **dataservices_settings | {"db": "test_dataservices"}
)
DATASERVICES_USER = dataservices_settings["username"]
TESTING = True
ENV = "test"

logging.debug(
    "\n\nApp test Database config:\n\
        Dataservices: %s\n\n",
    DSN_DATASERVICES_DATASETS,
)
