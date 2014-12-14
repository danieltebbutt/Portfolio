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
        
    def currentTickers(self):
        current = []
        for ticker, holding in self.holdings.iteritems():
            if holding.number > 0:
                current.append(ticker)
        return current                
        
    def totalDividends(self):
        dividends = 0
        for holding in self.holdings.values():
            dividends += holding.totalDividends()
        return dividends
        
    def totalProfit(self):
        profit = 0
        for holding in self.holdings.values():
            profit += holding.profit()
        return profit
    
    def capitalGain(self):
        gain = 0
        for holding in self.holdings.values():
            gain += holding.capitalGain()
        return gain
    