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

# wait for databases to boot up
echo 'sleep sleeeep..your eyes feels heavy..'
sleep 10
echo 'lets see if databases are working'

# load latest data into databases
docker exec -it geotest_nap_db_1 /bin/update-nap.sh
docker exec -it geotest_atlas_db_1 /bin/update-atlas.sh

sleep 2
# run da test

dc run --rm web_test python test_dataset.py
