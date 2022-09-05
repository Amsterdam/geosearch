for db in nap monumenten milieuthemas dataservices bag_v11 various_small_datasets;
do
echo "Granting access on $db"
docker-compose exec database psql -U postgres -d $db -c "CREATE USER insecure WITH PASSWORD 'insecure';"
docker-compose exec database psql -U postgres -d $db -c "GRANT ALL ON DATABASE $db TO insecure;"
docker-compose exec database psql -U postgres -d $db -c "CREATE DATABASE test_$db WITH TEMPLATE $db OWNER insecure;"
done
