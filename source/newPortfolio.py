# A portfolio is a collection of shares

from transaction import transaction
from holding import Holding

class NewPortfolio:

    def __init__(self):
        self.holdings = {}

    def applyTransaction(self, transaction):
        if not transaction.stock in self.holdings:
            self.holdings[transaction.ticker] = Holding(transaction.ticker)
            
        self.holdings[transaction.ticker].applyTransaction(transaction)
        
    def printSummary(self, date, prices):
        cash = 0        
        for ticker in self.holdings:
            holding = self.holdings[ticker]
            if holding.number != 0:
                if (holding.ticker, date) in prices:
                    print holding.toString(prices[(holding.ticker, date)])
                else:
                    print holding.toString(0)
            cash += holding.cash
        print u"Net invested: \N{pound sign}%.2f"%((0-cash)/100)