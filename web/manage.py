#!/usr/bin/env python
# Python
import datetime
import os
from pprint import pprint
import readline
import sys
# Packages
from flask import *
# Project
from datapunt_geosearch import app, db


def shell():
    """Start app shell"""
    os.environ['PYTHONINSPECT'] = 'True'

def run_server():
    app = create_app()
    app.run(debug=True, host='0.0.0.0')

def main():
    # Parsing args
    if len(sys.argv) == 1:
        shell()
    else:
        if sys.argv[1] == 'run':
            run_server()
        elif sys.argv[1] == 'shell':
            shell()
        else:
            print('Unkown command')

if __name__ == '__main__':
    main()
