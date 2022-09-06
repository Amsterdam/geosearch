#!/bin/sh

# Download geosearch databases into /tmp/downloaded_dbs
set -eu
set -x

rm -rf /tmp/downloaded_dbs
mkdir /tmp/downloaded_dbs
for db in nap monumenten milieuthemas dataservices bag_v11 various_small_datasets; do
    url="https://admin.data.amsterdam.nl/postgres/${db}_latest.gz"
    target="/tmp/downloaded_dbs/${db}_latest.gz"
    wget -O "$target" -nc "$url"
done
