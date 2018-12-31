import unittest
from price import Price
import datetime
from urlcache import urlcache

# Only 5 API calls permitted per minute

class PriceTestMethods(unittest.TestCase):

    def test_load_from_disk(self):  
        prices = {}
        Price.loadHistoricalPricesFromDisk(prices, "./source/test/price_test_1.txt")
        self.assertEqual(prices["A",datetime.date(1234,5,6)], 1)
        self.assertEqual(prices["A",datetime.date(2345,6,7)], 2)
        self.assertEqual(prices["B",datetime.date(1234,5,6)], 1.1)
        self.assertEqual(prices["C",datetime.date(2000,1,1)], 1.23)

    def test_load_current_from_web(self):
        urls = []
  
        currentTickers = ["BRK-B","NWBD.L"]

        for ticker in currentTickers:
            urls.append(Price.currentPriceUrl(ticker))

        urlCache = urlcache(urls)

        urlCache.cache_urls()
 
        prices = {}
        prices[('USD', datetime.date.today() - datetime.timedelta(1))] = 1.5
        Price.loadCurrentPricesFromWeb(currentTickers, prices, urlCache)

    def test_load_currency_from_web(self):
        urls = []

        currentTickers = ["EUR","USD"]

        for ticker in currentTickers:
            urls.extend(Price.historicalPricesUrl(ticker,
                                                  datetime.datetime(2011, 1, 1),
                                                  datetime.datetime(2018, 1, 1),
                                                  currency = True))
                                             
        urlCache = urlcache(urls)

        urlCache.cache_urls()

        prices = {}
        for ticker in currentTickers:
            Price.getCurrencyHistory(ticker, datetime.datetime(2011, 1, 1), datetime.datetime(2018, 1, 1), prices, urlCache)
  
        
