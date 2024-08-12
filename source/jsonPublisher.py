# Publish to json data files
import os
import webbrowser
import ftplib
import getpass
import pathlib
import io
from os import listdir
from os.path import isfile, join
import datetime
import posixpath
from abc import ABCMeta, abstractmethod
import configparser
import json

class jsonPublisher(object):

    def __init__(self, history, portfolio, investments):
        self.history = history
        self.portfolio = portfolio
        self.investments = investments
            
    def publishPublic(self, outputStream):
        data = {}
        data["current"] = []
        for ticker in sorted(self.portfolio.currentTickers(), key=lambda x: self.portfolio.holdings[x].value(), reverse = True):
            holding = self.portfolio.holdings[ticker]
            
            item = {}
            item["bought"] = [ d.strftime("%d %b %Y") for d in self.portfolio.holdings[ticker].activeBoughtDates() ]
            item["holding period"] = self.portfolio.holdings[ticker].averageHoldingPeriod()
            item["yearly returns"] = self.getYearReturns(ticker)
            item["name"] = self.investments[ticker].fullname
            item["ticker"] = ticker
            item["percent of total"] = (100 * holding.value() / self.portfolio.value())
            item["average purchase price"] = holding.averagePurchasePrice()
            item["current price"] = holding.price
            item["dividends"] = holding.perShareDividends(active = True)
            item["profit"] = 100 * holding.activeProfit() / holding.activeCost()
            item["annual profit"] = 0 if holding.averageHoldingPeriod() == 0 else \
                100 * ((1 + (holding.activeProfit() / holding.activeCost())) ** \
                (365.0 / holding.averageHoldingPeriod()) - 1)
            item["blog url"] = self.investments[ticker].blogUrl

            data["current"].append(item)

        purchases = []
        for ticker, holding in self.portfolio.holdings.items():
            purchases += holding.inactivePurchases()
            
        purchases.sort(key=lambda x: x.percent_profit(), reverse = True)

        data["previous"] = []
        for purchase in purchases:
            item = {}
            item["bought"] = purchase.date_bought.strftime("%d %b %Y")
            item["holding period"] = self.portfolio.holdings[ticker].averageHoldingPeriod()
            item["yearly returns"] = self.getYearReturns(ticker)
            item["name"] = self.investments[purchase.ticker].fullname
            item["ticker"] = purchase.ticker
            item["purchase price"] = purchase.purchase_price
            item["sale price"] = purchase.sale_price
            item["dividends"] = purchase.dividends_received
            item["profit"] = purchase.percent_profit()
            item["annual profit"] = purchase.annual_profit()
            item["blog url"] = self.investments[purchase.ticker].blogUrl
            item["date sold"] = [ d.strftime("%d %b %Y") for d in purchase.date_sold ]

            data["previous"].append(item)

        json.dump(data, outputStream)

    def publishPrivate(self, outputStream):
        pass
 
    def getYearReturns(self, ticker):
        returns = []
        initialDate = self.portfolio.holdings[ticker].firstBought()    
        for year in range(initialDate.year, datetime.date.today().year + 1):
            if year == initialDate.year:
                firstDate = initialDate
            else:        
                firstDate = datetime.date(year = year, month = 1, day = 1)
                
            if year == datetime.date.today().year:
                secondDate = datetime.date.today()
            else:
                secondDate = datetime.date(year = year + 1, month = 1, day = 1)
            
            firstPortfolio = self.history.getPortfolio(firstDate)
            secondPortfolio = self.history.getPortfolio(secondDate)
            
            profit = secondPortfolio.holdings[ticker].activeProfit() - firstPortfolio.holdings[ticker].activeProfit()
            percentProfit = profit / firstPortfolio.holdings[ticker].currentValue()
            
            returns.append({
                "year": year,
                "profit": percentProfit * 100
            })
                        
        return(returns)
