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
from itertools import chain

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

        data["overtime"] = []
        totalDays = datetime.date.today() - self.history.startDate()
            
        basis = self.history.basisForReturn()
        for days in chain(range(0, totalDays.days - 365, 28), 
                          range(totalDays.days - 365, totalDays.days - 50, 7),
                          range(totalDays.days - 50, totalDays.days, 1)):
            date = self.history.startDate() + datetime.timedelta(days = days)
            item = {}
            item["date"] = date.strftime("%d %b %Y")
            item["profit"] = 100 * self.history.getPortfolio(date).totalProfit() / basis
            item["size"] = 100 * self.history.getPortfolio(date).totalValue() / basis
            item["invested"] = 100 * self.history.getPortfolio(date).netInvested() / basis

            data["overtime"].append(item)

        json.dump(data, outputStream)

    def publishPrivate(self, outputStream):
        data = {}
        data["current"] = []

        for ticker in sorted(self.portfolio.currentTickers(), key=lambda x: self.portfolio.holdings[x].value(), reverse = True):
            holding = self.portfolio.holdings[ticker]
            
            item = {}
            item["ticker"] = ticker
            item["number"] = holding.number
            item["cost"] = holding.activeCost() / 100
            item["value"] = holding.currentValue() / 100
            item["dividends"] = holding.totalDividends() / 100
            item["capital gain"] = (holding.currentValue() - holding.activeCost()) / 100
            item["profit"] = holding.activeProfit() / 100
        
            data["current"].append(item)


        data["summary"] = {
            "invested"    : self.portfolio.netInvested() / 100,
            "value"       : self.portfolio.totalValue() / 100,
            "capital gain": self.portfolio.capitalGain() / 100,
            "profit"      :  self.portfolio.totalProfit() / 100
        }

        # Provide data per-year and for the last 90, 30, 7 and 2 days
        date_pairs = [("all", self.history.startDate(),datetime.date.today())]
        for year in range(self.history.startDate().year, datetime.date.today().year):
            date_pairs.append(("%d"%year,
                               datetime.date(year=year, month=1, day=1), 
                               datetime.date(year=year + 1, month=1, day=1)))
        date_pairs.append(("%d"%datetime.date.today().year,
                           datetime.date(year=datetime.date.today().year, month=1, day=1),
                           datetime.date.today()))
        for period in 90, 30, 7, 1:
            date_pairs.append(("%d days"%period,datetime.date.today() - datetime.timedelta(days = period + 1), datetime.date.today() - datetime.timedelta(days = 1)))
        
        data["periods"] = {}

        for period, startDate, endDate in date_pairs:
            startPortfolio = self.history.getPortfolio(startDate)
            endPortfolio = self.history.getPortfolio(endDate)

            totalProfit = (endPortfolio.totalProfit() - startPortfolio.totalProfit()) / 100
            basisForReturn = self.history.basisForReturn(startDate, endDate) / 100
            percent_return = 100 * totalProfit / basisForReturn
            capital_gain = (endPortfolio.capitalGain() - startPortfolio.capitalGain()) / 100

            item = {}
            item["period"] = period
            item["profit"] = totalProfit
            item["basis"] = basisForReturn
            item["return"] = percent_return
            item["capital"] = capital_gain
            item["dividends"] = (endPortfolio.totalDividends() - startPortfolio.totalDividends()) / 100
            item["holdings"] = []

            for ticker, endHolding in endPortfolio.holdings.items():
                startHolding = None
                if ticker in startPortfolio.holdings:
                    startHolding = startPortfolio.holdings[ticker]
                    
                if not startHolding:
                    startProfit = 0
                    startCapitalGain = 0
                    startTotalDividends = 0
                elif startHolding.profit() != endHolding.profit() or startHolding.number != 0 or endHolding.number != 0:
                    startProfit = startHolding.profit()
                    startCapitalGain = startHolding.capitalGain()
                    startTotalDividends = startHolding.totalDividends()
                else:
                    startProfit = None
                    
                if startProfit != None:
                    item["holdings"].append(
                        { "ticker"    : ticker,
                          "capital"   : (endHolding.capitalGain() - startCapitalGain) / 100,
                          "dividends" : (endHolding.totalDividends() - startTotalDividends) / 100,
                          "profit"    : (endHolding.profit() - startProfit) / 100 } )

            data["periods"][period] = item

        json.dump(data, outputStream)
 
    def getYearReturns(self, ticker):
        returns = []
        initialDate = self.portfolio.holdings[ticker].firstBought()
        if not initialDate:
            return(0)
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
