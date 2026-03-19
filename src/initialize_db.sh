#!/bin/bash
# Run when INITIALIZE_DB parameter is set and migrations are available.
if ! ./src/manage.py migrate --check && "$INITIALIZE_DB" = "true";
then
    uv run ./src/manage.py migrate;
fi
