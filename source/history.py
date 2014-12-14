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
        