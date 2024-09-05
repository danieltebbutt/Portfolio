#
# Loads prices
#

import os
import datetime
import re
import operator
import json
import sys, traceback
from abc import ABCMeta, abstractmethod

from .price import Price

class priceLoader(object):

    def __init__(self, stockTickerList = None, currencyTickerList = None):
        self.stockTickerList = stockTickerList
        self.currencyTickerList = currencyTickerList

    @abstractmethod
    def fixRawPrice(self, ticker, price, priceDate, prices):
        pass
    
    @abstractmethod
    def getCurrentPrices(self):
        pass
