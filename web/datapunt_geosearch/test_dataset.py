import unittest

import datasource


# tested running atlas_import database with latest atlas backup:
# docker exec atlasbackend_database_1 /bin/update-atlas.sh
# python test_dataset.py
# > Ran 1 test in 0.062s


class TestAtlasDataset(unittest.TestCase):
    def test_query(self):
        x = 120993
        y = 485919

        ds = datasource.AtlasDataSource()
        results = ds.query(x, y)

        self.assertEqual(len(results['result']['features']), 7)

    def test_query_wgs84(self):
        x = 52.36011
        y = 4.88798

        ds = datasource.AtlasDataSource()
        results = ds.query(x, y, rd=False)

        self.assertEqual(len(results['result']['features']), 7)


class TestNapDataset(unittest.TestCase):
    def test_query(self):
        x = 120535.2
        y = 486376.3

        ds = datasource.NapMeetboutenDataSource()
        results = ds.query(x, y)

        self.assertEqual(len(results['result']['features']), 1)


if __name__ == '__main__':
    unittest.main()
