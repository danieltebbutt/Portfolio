#
# Loads prices from yahoo finance
#
import os
from datetime import date
import re
import operator
from forex_python.converter import CurrencyRates
import json
import sys, traceback
import yfinance as yf

from .priceLoader import priceLoader

class yfPriceLoader(priceLoader):

    tickerMap = {
        "Euro" : "GBPEUR=X",
        "USD" : "GBPUSD=X",
        "NOK" : "GBPNOK=X"
    }
    invertedTickerMap =  {v: k for k, v in tickerMap.items()}

    def getCurrentPrices(self, prices):
        allTickers = [ self.tickerMap[x] if x in self.tickerMap else x for x in self.currencyTickerList + self.stockTickerList ]
        data = yf.download(allTickers, period='1d')
        for ticker in allTickers:
            price = float(data['Close', ticker])
            ticker = self.invertedTickerMap[ticker] if ticker in self.invertedTickerMap else ticker
            self.fixRawPrice(ticker, price, date.today(), prices)
            prices[(ticker, date.today())] = price

