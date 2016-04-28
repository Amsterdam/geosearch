# Packages
from flask import Flask

app = Flask('geosearch')
# Define the view for the search
@app.route('/search/geo')
def geo_search():
    return 'Geo search'

