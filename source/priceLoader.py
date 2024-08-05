#
# Loads prices
#

import os
import datetime
import re
import operator
from forex_python.converter import CurrencyRates
import json
import sys, traceback
from abc import ABCMeta, abstractmethod

from .price import Price

class priceLoader(object):

    def __init__(self, stockTickerList = None, currencyTickerList = None):
        self.stockTickerList = stockTickerList
        self.currencyTickerList = currencyTickerList

    def fixRawPrice(self, ticker, price, priceDate, prices):
        if ticker.find("SLXX") != -1:
            price *= 100
        if ticker.find("CPT") != -1:
            price *= 100
        if ticker.find("IS15") != -1 and price < 1000:
            price *= 100
        if ticker.find("IS15") != -1 and price > 12000:
            price = 0
        if ticker.find("BRK-B") != -1:
            lastDay = priceDate
            while ("USD", lastDay) not in prices:
                lastDay = lastDay - datetime.timedelta(days = 1)
            price *= prices[("USD", lastDay)]
            if price > 10000 and priceDate < datetime.date(year=2010,month=2,day=1):
                price /= 50
        if ticker.find("TEG") != -1:
            lastDay = priceDate
            while ("Euro", lastDay) not in prices:
                lastDay = lastDay - datetime.timedelta(days = 1)
            price *= prices[("Euro", lastDay)]            
        if "NWBD" in ticker and price > 800:
            price /= 100
        return price

    @abstractmethod
    def getCurrentPrices(self):
        pass
