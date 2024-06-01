#!/bin/bash
# Add extra database for running tests
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE DATABASE test_dataservices;
    \c test_dataservices;
    CREATE EXTENSION postgis;
	GRANT ALL PRIVILEGES ON DATABASE test_dataservices TO postgres;
EOSQL