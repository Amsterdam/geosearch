# Download geosearch databases into /tmp/downloaded_dbs
rm -rf /tmp/downloaded_dbs
rm /tmp/*_latest.gz
for db in nap monumenten milieuthemas dataservices bag_v11 various_small_datasets;
do
  download-db.sh $db;
done
mkdir /tmp/downloaded_dbs
mv /tmp/*_latest.gz /tmp/downloaded_dbs
ls -lah /tmp/downloaded_dbs
