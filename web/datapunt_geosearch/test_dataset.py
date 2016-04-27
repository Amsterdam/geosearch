import unittest

import datasource


# tested running atlas_import database with latest atlas backup:
# docker exec atlasbackend_database_1 /bin/update-atlas.sh
# python test_dataset.py
# > Ran 1 test in 0.062s

# test data

# x = 111176.768947226
# y = 467563.287934656
# rd = True

# x =52.369604918845354
# y = 4.896307341338379
# rd = False

x = 120993
y = 485919
rd = True


class TestAtlasDataset(unittest.TestCase):
    def test_query(self):
        ds = datasource.AtlasDataSource()
        results = ds.query(x, y, rd=rd)

        self.assertEqual(len(results), 10)


if __name__ == '__main__':
    unittest.main()
