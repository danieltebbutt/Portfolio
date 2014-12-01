# A portfolio is a collection of shares

from transaction import transaction
from holding import Holding

class NewPortfolio:

    def __init__(self, date):
        self.holdings = {}
        self.date = date

    def applyTransaction(self, transaction):
        if not transaction.stock in self.holdings:
            self.holdings[transaction.ticker] = Holding(transaction.ticker)
            
        self.holdings[transaction.ticker].applyTransaction(transaction)
        
    def notePrices(self, prices):
        for ticker in self.holdings:
            holding = self.holdings[ticker]
            if (holding.ticker, self.date) in prices:
                holding.notePrice(prices[(holding.ticker, self.date)])                    
    
    def value(self):
        value = 0
        for holding in self.holdings.values():
            value += holding.currentValue()
        return value
    
    def contains(self, ticker):
        return self.holdings[ticker].number > 0
    
    def cash(self):
        cash = 0        
        for holding in self.holdings.values():
            cash += holding.cash
        return cash
        
    def netInvested(self):
        return (0 - self.cash())
        