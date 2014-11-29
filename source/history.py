#
# A history covers all transactions over a set period
#

import re
import datetime

from transaction import transaction
from newPortfolio import NewPortfolio

class History:

    def __init__(self, transactions):
        self.transactions = transactions

    def getPortfolio(self, date):
        portfolio = NewPortfolio()
        for transaction in self.transactions:
            if transaction.date < date:
                portfolio.applyTransaction(transaction)
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
       