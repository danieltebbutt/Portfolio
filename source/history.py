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