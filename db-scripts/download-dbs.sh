#!/bin/bash
# Download geosearch databases into /tmp
rm /tmp/*_latest.gz
for db in nap monumenten milieuthemas dataservices bag_v11 various_small_datasets;
do
  download-db.sh $db;
done
ls -lah /tmp/*_latest.gz
