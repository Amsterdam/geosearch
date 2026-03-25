# Geosearch

Geospatial search acros datasets.

# Installation

Requirements:

* Python >= 3.14
* Recommended: Docker/Docker Compose (or uv for local installs)

## Using Docker Compose

Run docker compose:

```shell
docker compose up --watch
```

Navigate to `localhost:8097/pulse`.

## Using Local Python

Install all packages with:

```shell
make install  # installs all packages and pre-commit hooks.
```

Start the Django application:

```shell
uv run uvicorn geosearch.asgi:application --host 0.0.0.0 --port 8097
```

# Developer Notes

Run `make` in the `src` folder to have a help-overview of all common developer tasks.

## Package Management

The packages are managed with *uv*.

To add a package, run `uv add <package>`.
This will update the lockfile  `uv.lock` that's used for installs.

To upgrade all packages, run `make upgrade`, followed by `make install` and `make test`.
Or at once if you feel lucky: `make upgrade install test`.

## Environment Settings

Consider using *direnv* for automatic activation of environment variables.
It automatically sources an ``.envrc`` file when you enter the directory.
This file should contain all lines in the `export VAR=value` format.

In a similar way, *uv* helps to install the exact Python version,
and will automatically activate a virtualenv and use it when you run commands using `uv run`.

## Debugging

To debug a running container, run docker compose with the extra debug compose file:

```
    docker compose -f docker-compose.yml -f docker-compose.debug.yml up -d
```

In your `.vscode` folder, copy the `launch.example.json` to `launch.json`. Ensure that the paths are matching with what you
have (especially packages in your virtualenv).

Start the debugger through the Run and Debug menu. The debugger is called "Python Debugger:
Remote Attach". You can now add breakpoints.

## Available endpoints

The following endpoints are available:

| Endpoint                | Description                                                                        |
|-------------------------|------------------------------------------------------------------------------------|
| `/pulse`                | Simple health check to verify the application is running                           |
| `/health-check`         | Health check which verifies connection to the database                             |
| `/geosearch/catalogus/` | Used to receive a list of versioned dataset/tables which can be used for Geosearch. |
