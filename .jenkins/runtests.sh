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
dc up -d bag_db
dc up -d nap_db
dc up -d milieuthemas_db
dc up -d tellus_db
dc up -d monumenten_db
dc up -d grondexploitatie_db

# wait for databases to boot up
sleep 10
echo "let's see if databases are working"

# load latest data into databases
# TODO only tables!
dc exec -T nap_db /bin/update-db.sh nap
dc exec -T bag_db /bin/update-db.sh bag
dc exec -T milieuthemas_db /bin/update-db.sh milieuthemas
dc exec -T tellus_db /bin/update-db.sh tellus
dc exec -T monumenten_db /bin/update-db.sh monumenten
dc exec -T grondexploitatie_db /bin/update-db.sh grondexploitatie

sleep 1m
# run da test

dc run --rm web_test python test_dataset.py
