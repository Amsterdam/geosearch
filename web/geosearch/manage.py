#!/usr/bin/env python

# Python
import os
import sys


def shell():
    """Start app shell"""
    os.environ["PYTHONINSPECT"] = "True"


def help_txt():
    print(
        "shell - start an interactive shell\n"
        "create - create the geoindex in elastic\n"
        "recreate - drop the old index and create a new one in elastic"
    )


def main():
    # Parsing args
    if len(sys.argv) == 1:
        shell()
    else:
        if sys.argv[1] == "shell":
            shell()
        elif sys.argv[1] == "help":
            help_txt()
        else:
            print("Unkown command, options:")
            help_txt()


if __name__ == "__main__":
    main()
