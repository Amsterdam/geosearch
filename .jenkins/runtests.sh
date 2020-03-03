#!/bin/bash

set -e
set -u

DIR="$(dirname $0)"

dc() {
	docker-compose -p geotest -f ${DIR}/docker-compose-test.yml $*;
}

trap 'dc kill ; dc rm -f' EXIT

dc build --pull

# create test databases
dc up -d bag_v11_db
dc up -d nap_db
dc up -d milieuthemas_db
# dc up -d tellus_db
dc up -d monumenten_db
dc up -d various_small_datasets_db
dc up -d dataservices_db

# wait for databases to boot up
sleep 10
echo "let's see if databases are working"

# load latest data into databases
# TODO only tables!
dc exec -T nap_db /bin/update-db.sh nap
# Allow Bag DB update to fail, as restore generates errors due to not existing roles
dc exec -T bag_v11_db /bin/update-db.sh bag_v11 || true
dc exec -T milieuthemas_db /bin/update-db.sh milieuthemas
# dc exec -T tellus_db /bin/update-db.sh tellus
dc exec -T monumenten_db /bin/update-db.sh monumenten
dc exec -T various_small_datasets_db /bin/update-db.sh various_small_datasets

sleep 1m
# run da test

echo "Testing."
dc run --rm web_test py.test -s .
echo "Done testing"
