import unittest
from pricetest import PriceTestMethods

suite = unittest.TestLoader().loadTestsFromTestCase(PriceTestMethods)
unittest.TextTestRunner(verbosity=2).run(suite)

