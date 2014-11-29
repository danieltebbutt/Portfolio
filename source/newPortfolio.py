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
        
    def notePrices(self, date, prices):
        for ticker in self.holdings:
            holding = self.holdings[ticker]
            if (holding.ticker, date) in prices:
                holding.notePrice(date, prices[(holding.ticker, date)])                    
    
    def value(self):
        value = 0
        for holding in self.holdings.values():
            value += holding.currentValue()
        return value
    
    def printSummary(self):
        cash = 0        
        for holding in self.holdings.values():
            if holding.number != 0:              
                print holding.toString()
            cash += holding.cash
        print u"Net invested:  \N{pound sign}%.2f"%((0-cash)/100)
        print u"Current value: \N{pound sign}%.2f"%self.value()
        
    def printPurchases(self):
        purchases = []
        for holding in self.holdings.values():
            purchases.extend(holding.purchases)
        for purchase in reversed(sorted(purchases, key=lambda purchase: purchase.percent_profit())):
            print purchase.toString()