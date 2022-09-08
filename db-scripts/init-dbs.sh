#!/bin/bash
# Script for downloading, installing and configuring the roles for
# databases used in development and tests of geosearch
for db in nap monumenten milieuthemas dataservices bag_v11 various_small_datasets;
do
echo "Downloading $db"
download-db.sh $db;
echo "Restoring $db"
update-db.sh $db;
echo "Granting access on $db"
psql -U postgres -d $db -c "GRANT ALL ON DATABASE $db TO $POSTGRES_USER;";
psql -U postgres -d $db -c "CREATE DATABASE test_$db WITH TEMPLATE $db OWNER $POSTGRES_USER;";
done
