#
# A history covers all transactions over a set period
#

import re
import datetime
from datetime import timedelta

from .transaction import transaction
from .newPortfolio import NewPortfolio

class History:

    def __init__(self, transactions, prices = {}):
        self.transactions = transactions
        self.prices = prices

    def getPortfolio(self, portfolioDate):
        portfolio = NewPortfolio(portfolioDate)
        for transaction in self.transactions:
            if transaction.date <= portfolioDate:
                portfolio.applyTransaction(transaction)
        portfolio.notePrices(self.prices)
        return portfolio

    def firstHeld(self, ticker):
        for transaction in self.transactions:
            if transaction.ticker == ticker:
                return transaction.date

    def lastHeld(self, ticker):
        if self.getPortfolio(datetime.date.today()).contains(ticker):
            return datetime.date.today()
        else:
            for transaction in reversed(self.transactions):
                if transaction.ticker == ticker and transaction.action == "SELL":
                    return transaction.date

    def notePrices(self, prices):
        self.prices = prices

    def currentTickers(self):
        return self.activeTickers()

    def activeTickers(self, startDate = None, endDate = None):
        if not startDate:
            startDate = datetime.date.today()

        tickers = self.getPortfolio(startDate).currentTickers()

        if endDate:
            transactions = self.getTransactions(startDate, endDate, actions = ["BUY"])
            for transaction in transactions:
                if transaction.ticker not in tickers:
                    tickers.append(transaction.ticker)
        return tickers

    def getPortfolios(self, startDate, endDate):
        currentDate = startDate

        portfolio = self.getPortfolio(startDate)

        for transaction in self.transactions:
            while currentDate < transaction.date and currentDate < endDate:
                portfolio.date = currentDate
                portfolio.notePrices(self.prices)
                yield portfolio
                currentDate += datetime.timedelta(days = 1)
            if transaction.date > endDate:
                break
            if transaction.date >= startDate:
                portfolio.applyTransaction(transaction)
        while currentDate <= endDate:
            portfolio.date = currentDate
            portfolio.notePrices(self.prices)
            yield portfolio
            currentDate += timedelta(days = 1)

    def basisForReturn(self, startDate, endDate):
        numerator = 0
        portfolio = self.getPortfolio(startDate)
        modifier = portfolio.value() - portfolio.netInvested()
        for portfolio in self.getPortfolios(startDate, endDate):
            numerator += portfolio.netInvested() + modifier

        return numerator / ((endDate - startDate).days + 1)

    def averageValue(self, startDate, endDate):
        numerator = 0
        portfolio = self.getPortfolio(startDate)
        for portfolio in self.getPortfolios(startDate, endDate):
            numerator += portfolio.value()

        return numerator / ((endDate - startDate).days + 1)

    def peakValue(self, startDate = None, endDate = None):
        if not startDate:
            startDate = self.startDate()
        if not endDate:
            endDate = self.endDate()

        peak = 0
        for portfolio in self.getPortfolios(startDate, endDate):
            peak = max(peak, portfolio.totalValue())

        return peak

    def startDate(self):
        return self.transactions[0].date

    def endDate(self):
        return self.transactions[-1].date

    def peakInvested(self, startDate = None, endDate = None):
        if not startDate:
            startDate = self.startDate()
        if not endDate:
            endDate = self.endDate()

        peak = 0
        for portfolio in self.getPortfolios(startDate, endDate):
            peak = max(peak, portfolio.netInvested())

        return peak

    def price(self, ticker, date):
        return self.prices[(ticker, date)]

    def getTransactions(self, startDate, endDate = None, ticker = None, actions = transaction.ACTIONS):
        if not startDate:
            startDate = self.startDate()
        if not endDate:
            endDate = datetime.date.today()
        for transaction in self.transactions:
            if transaction.date > endDate:
                break
            elif transaction.date >= startDate and \
                 (not ticker or ticker == transaction.ticker) and \
                 transaction.action in actions:
                yield transaction

    def dividendsReceived(self, startDate, endDate, exchangeTicker = None):
        total = 0
        for transaction in self.getTransactions(startDate, endDate, None, "DIV"):
            dividend = transaction.number * transaction.price
            if exchangeTicker:
                dividend /= self.price(exchangeTicker, transaction.date)
            total += dividend
        return total

