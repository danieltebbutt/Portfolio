#
# A history covers all transactions over a set period
#

import re
import datetime

from transaction import transaction
from newPortfolio import NewPortfolio

class History:

    def __init__(self, transactions, prices = {}):
        self.transactions = transactions
        self.prices = prices

    def getPortfolio(self, portfolioDate):
        portfolio = NewPortfolio(portfolioDate)
        for transaction in self.transactions:
            if transaction.date < portfolioDate:
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
        return self.getPortfolio(datetime.date.today()).currentTickers()
        
    def basisForReturn(self, startDate, endDate):
        # Get a portfolio for the start of the period
        portfolio = self.getPortfolio(startDate) 
        currentDate = startDate
        numerator = 0
        
        # We want the average net invested over the period, but must include
        # any accumulated profit at the start date
        modifier = portfolio.value() - portfolio.netInvested()
        for transaction in self.transactions:
            while currentDate < transaction.date and currentDate < endDate:
                numerator += portfolio.netInvested() + modifier
                currentDate += datetime.timedelta(days = 1)
            if transaction.date > endDate:
                break
            if transaction.date >= startDate:
                portfolio.applyTransaction(transaction)
        
        # If we've run out of transactions then spin forwards to the end of the period.
        while currentDate < endDate:
            numerator += portfolio.netInvested() + modifier
            currentDate += datetime.timedelta(days = 1)
                    
        return numerator / ((endDate - startDate).days)

    def peakValue(self):
        return 10000000