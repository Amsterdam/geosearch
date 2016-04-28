"""
The elastic search communication library.
It is a utility thin wrapper around the python elastic search library

Tasks:
    - Create index
    - Destroy index
    - Search in radius
    - Search in polygon

"""
import requests


class Elastic(object):

    def __init__(self, host='0.0.0.0:9200', index='geo'):
        """Init the elastic connection"""
        self.host = host
        self.index = index
        self.request_url = 'http://{0}/{1}/'.format(host, index)

    def create_index(self):
        """
        Creates the geo index
        A check is made to make sure that the
        index does not yet exits. If the index
        already exists, a False is returend

        Returns True if the index is created,
                False otherwise
        """
        success = False  # Pessimism
        # Checking if the index exists
        r = requests.head(self.request_url)
        if r.status_code == 404:
            # Index does not exsits, it is safe to create it
            # @TODO add support for index setting
            try:
                r = requests.put(self.request_url)
                if r.status_code < 300:
                    success = True
            except Exception as e:
                print(e)
        return success

    def delete_index(self):
        """Delete the index"""
        try:
            requests.delete(self.request_url)
        except Exception as e:
            print(e)
            return False
        return True

    def search_radius(self, point, radius, types=None, exclude=False):
        """
        Perform a geo query search at point with a radius of radiu

        point: An array, in GeoJSON style of the point to check around
                GeoJSON is [lon, lat]
        radius: A number (int, float and str accepted) of the distance in
                meters

        The function has two optional parameters:
        types: A list of types to use in the query. This is to limit the
                result set.
        exclude: Reverse the list of types to use as exclude types instead of
                include types
        """
        # Verifying input
        # Checking that radius is a number and convert it to m string
        try:
            radius = str(float(radius)) + 'm'
        except ValueError:
            # The radius is not a float number
            return False
        # Checking that the point is 2 items long
        if len(point) != 2:
            return False
        # The query dict
        # https://www.elastic.co/guide/en/elasticsearch/reference/2.3/query-dsl-geo-distance-query.html
        query = {
            "bool": {
                "must": {
                    "match_all": {}
                },
                "filter": {
                    "geo_distance": {
                        "distance": radius,
                        "center" : point,
                        "distance_type": "plane"
                    }
                }
            }
        }
        r = requests.post('http://' + self.hosts + '/' + self.index_name, data=query)
        return r.json()

