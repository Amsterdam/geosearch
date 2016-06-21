import unittest
import datapunt_geosearch
from datapunt_geosearch import config

class ApiTest(unittest.TestCase):

    def setUp(self):
       self.app = datapunt_geosearch.create_app(config=config)

    def test_cors_header(self):
        with self.app.test_client() as client:
            resp = client.get('/nap/?lat=52.7&lon=4.8')
            self.assertTrue('Access-Control-Allow-Origin' in resp.headers)
            self.assertEquals('*', resp.headers['Access-Control-Allow-Origin'])

if __name__ == '__main__':
    unittest.main()
