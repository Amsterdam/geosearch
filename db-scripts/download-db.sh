#!/bin/bash
TARGET_FILE="/tmp/$1_latest.gz"
DOWNLOAD_URL="https://$OS_TENANT_ID.objectstore.eu/Dataservices/geosearch-fixtures/${1}_latest.gz"

if [[ ! -f "${TARGET_FILE}" ]]; then
    echo "$1_latest.gz file does not exist, downloading backup"

    wget --header="X-Auth-Token: $OS_AUTH_TOKEN" -O "${TARGET_FILE}" -nc "${DOWNLOAD_URL}";
fi

