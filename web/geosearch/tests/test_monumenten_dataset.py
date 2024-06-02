import unittest

from flask import current_app as app
from psycopg2 import Error as Psycopg2Error

from datapunt_geosearch import datasource
from datapunt_geosearch.db import retry_on_psycopg2_error


class TestMonumentenDataset(unittest.TestCase):

    def test_retry_on_psycop2_error_walks_out_of_range(self):
        """Confirm that retry_on_psycopg2_error is\
             not walking out of loop before raising last error"""

        @retry_on_psycopg2_error
        def test_func(*args, **kwargs):
            raise Psycopg2Error("TEST")

        with self.assertRaises(Psycopg2Error) as e:
            test_func("whoo")

        self.assertEqual(e.exception.args, ("TEST",))


if __name__ == "__main__":
    unittest.main()
