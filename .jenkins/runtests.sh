#!/bin/bash

set -e
set -u

DIR="$(dirname $0)"

dc() {
	docker-compose -p geotest -f ${DIR}/docker-compose.yml $*;
}

#trap 'dc kill ; dc rm -f' EXIT

dc build --pull

# create test databases
dc up -d atlas_db
dc up -d nap_db
dc up -d milieu_db
dc up -d tellus_db
dc up -d monumenten_db

# wait for databases to boot up
sleep 10
echo "let's see if databases are working"

# load latest data into databases
dc exec -T nap_db /bin/update-db.sh nap
dc exec -T atlas_db /bin/update-db.sh atlas
dc exec -T milieu_db /bin/update-db.sh milieuthemas
dc exec -T tellus_db /bin/update-db.sh tellus
dc exec -T monumenten /bin/update-db.sh monumenten

sleep 2
# run da test

dc run --rm web_test python test_dataset.py
