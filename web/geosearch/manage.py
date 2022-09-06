#!/usr/bin/env python

# Python
import os
import sys

from datapunt_geosearch import create_app


def shell():
    """Start app shell"""
    os.environ["PYTHONINSPECT"] = "True"


def run_server():
    from datapunt_geosearch import config

    app = create_app(config)
    app.run(debug=True, host="localhost", port=8000)


def run_server_prod():
    # Starts the server with prod settings
    from datapunt_geosearch import config

    app = create_app(config)
    app.run(host="0.0.0.0", port=8000)


def help_txt():
    print(
        "run - start dev server\n"
        "shell - start an interactive shell\n"
        "create - create the geoindex in elastic\n"
        "recreate - drop the old index and create a new one in elastic"
    )


def main():
    # Parsing args
    if len(sys.argv) == 1:
        shell()
    else:
        if sys.argv[1] == "run":
            run_server()
        elif sys.argv[1] == "run_prod":
            run_server_prod()
        elif sys.argv[1] == "shell":
            shell()
        elif sys.argv[1] == "help":
            help_txt()
        else:
            print("Unkown command, options:")
            help_txt()


if __name__ == "__main__":
    main()
