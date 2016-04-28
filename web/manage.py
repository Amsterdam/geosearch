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
from datapunt_geosearch import create_app
from datapunt_geosearch.elastic import Elastic


def shell():
    """Start app shell"""
    os.environ['PYTHONINSPECT'] = 'True'

def run_server():
    app = create_app()
    app.run(debug=True, host='0.0.0.0')

def recreate_index():
    # Deleting the current index and recreating it
    es = Elastic()
    success = es.delete_index()
    if success:
        success = es.create_index()
    if not success:
        print ("Failed to delete index and recreate index")

def main():
    # Parsing args
    if len(sys.argv) == 1:
        shell()
    else:
        if sys.argv[1] == 'run':
            run_server()
        elif sys.argv[1] == 'shell':
            shell()
        elif sys.argv[1] == 'recreate':
            recreate_index()
        else:
            print('Unkown command')

if __name__ == '__main__':
    main()
