import logging

from datapunt_geosearch.base_config import DATAPUNT_API_URL  # noqa
from datapunt_geosearch.base_config import (  # noqa: F401
    DATABASE_SET_ROLE,
    db_connection_string,
    get_db_settings,
)

dataservices_settings = get_db_settings("dataservices")
DSN_DATASERVICES_DATASETS = db_connection_string.format(**dataservices_settings)
DATASERVICES_USER = dataservices_settings["username"]


logging.debug(
    "\n\nApp Database config:\n\
        Dataservices: %s\n\
        Role switching %s\n\n",
    DSN_DATASERVICES_DATASETS,
    "active" if DATABASE_SET_ROLE else "inactive",
)
