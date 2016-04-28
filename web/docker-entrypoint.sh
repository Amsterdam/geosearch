#!/usr/bin/env bash

set -e
set -u

PYTHON=$(which python3 || which python)

echo Starting server
uwsgi --ini uwsgi.ini
