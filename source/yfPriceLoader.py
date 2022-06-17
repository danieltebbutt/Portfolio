#
# Loads prices from yahoo finance
#
import os
from datetime import datetime, date
import re
import operator
from forex_python.converter import CurrencyRates
import json
import sys, traceback
import yfinance as yf

from .priceLoader import priceLoader

class yfPriceLoader(priceLoader):

    tickerMap = {
        "Euro" : "EURGBP=X",
        "USD" : "USDGBP=X",
        "NOK" : "NOKGBP=X"
    }
    invertedTickerMap =  {v: k for k, v in tickerMap.items()}

    def fixRawPrice(self, ticker, price, priceDate, prices):
        if "=X" in ticker:
            price *= 100
        if "NWBD" in ticker:
            price *= 100
        if "BRK-B" in ticker:
            lastDay = priceDate
            while ("USD", lastDay) not in prices:
                lastDay = lastDay - datetime.timedelta(days = 1)
            price *= prices[("USD", lastDay)]
            if price > 10000 and priceDate < date(year=2010,month=2,day=1):
                price /= 50
        if ticker.find("TEG") != -1:
            lastDay = priceDate
            while ("Euro", lastDay) not in prices:
                lastDay = lastDay - datetime.timedelta(days = 1)
            price *= prices[("Euro", lastDay)]  
        return price
        

    def getCurrentPrices(self, prices):
        allTickers = [ self.tickerMap[x] if x in self.tickerMap else x for x in self.currencyTickerList + self.stockTickerList ]
        data = yf.download(allTickers, period='5d')
        for ticker in allTickers:
            try:
                price = float(data.apply(lambda x: x[x.notnull()].values[-1])['Close'][ticker])
                price = self.fixRawPrice(ticker, price, date.today(), prices)
                ticker = self.invertedTickerMap[ticker] if ticker in self.invertedTickerMap else ticker
                prices[(ticker, date.today())] = price
            except Exception:
                print("Error!")
                traceback.print_exception(*sys.exc_info())

