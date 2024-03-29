import logging

from datapunt_geosearch.base_config import (  # noqa: F401
    CLOUD_ENV,
    DATABASE_SET_ROLE,
    DATAPUNT_API_URL,
    DEFAULT_SEARCH_DATASETS,
    DSN_ADMIN_USER,
    JW_KEYSET,
    JWKS,
    JWKS_SIGNING_ALGORITHMS,
    JWKS_TEST_KEY,
    JWKS_URL,
    db_connection_string,
    get_db_settings,
)

DSN_BAG = db_connection_string.format(**get_db_settings("bag_v11"))
DSN_NAP = db_connection_string.format(**get_db_settings("nap"))
DSN_MILIEU = db_connection_string.format(**get_db_settings("milieuthemas"))
DSN_MONUMENTEN = db_connection_string.format(**get_db_settings("monumenten"))
DSN_VARIOUS_SMALL_DATASETS = db_connection_string.format(
    **get_db_settings("various_small_datasets")
)

dataservices_settings = get_db_settings("dataservices")
DSN_DATASERVICES_DATASETS = db_connection_string.format(**dataservices_settings)
DATASERVICES_USER = dataservices_settings["username"]


logging.debug(
    "\n\nApp Database config:\n\
         Bag: %s\n\
         Nap: %s\n\
         Milieu: %s\n\
         Monumenten: %s\n\
        Various Small Datasets: %s\n\
        Dataservices: %s\n\
        Role switching %s\n\n",
    DSN_BAG,
    DSN_NAP,
    DSN_MILIEU,
    DSN_MONUMENTEN,
    DSN_VARIOUS_SMALL_DATASETS,
    DSN_DATASERVICES_DATASETS,
    "active" if DATABASE_SET_ROLE else "inactive",
)
