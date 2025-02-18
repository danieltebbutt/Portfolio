# A holding is an individual shareholding

from .transaction import transaction
from .purchase import purchase
import math

class Holding:

    def __init__(self, ticker):
        self.ticker = ticker
        self.number = 0
        self.cash = 0
        self.purchases = []
        self.price = 0

    def applyTransaction(self, transaction):
        # First apply the transaction to the list of purchases
        if transaction.action == "BUY":
            self.purchases.append(purchase(transaction.ticker, transaction.number, transaction.date, transaction.price))
        elif transaction.action == "INT" or transaction.action == "DIV":
            pass
        elif transaction.action == "RIGHTS":
            # Applied in proportion to the current share numbers in each purchase
            for item in self.purchases:
                item.credit_rights(transaction.number / self.number, transaction.price)
        elif transaction.action == "EXDIV":
            # Again, applied in proportion to purchases
            for item in self.purchases:
                item.dividend(self.number, transaction.price)
        elif transaction.action == "SCRIP":
            for item in self.purchases:
                item.scrip(transaction.number / self.number)
        elif transaction.action == "SELL":
            # Apply to recent purchases first.
            number = transaction.number
            for item in reversed(self.purchases):
                number = item.sell(number, transaction.price, transaction.date)
            
        # Now apply it to the entire holding
        (self.number, self.cash) = transaction.applyTransaction(self.number, self.cash)

    def notePrice(self, price):
        self.price = price
        for purchase in self.purchases:
            purchase.note_price(price)
    
    def value(self):
        return self.currentValue()
    
    def currentValue(self):
        return (self.number * self.price)
    
    def activePurchases(self):
        active = []
        for purchase in self.purchases:
            if purchase.number_left() > 0:
                active.append(purchase)
        return active
    
    def inactivePurchases(self):
        return list(set(self.purchases) - set(self.activePurchases()))
    
    def toString(self):        
        return "%8d %6s, net cost \N{pound sign}%8.2f, value = \N{pound sign}%8.2f, profit = \N{pound sign}%8.2f"%(\
               self.number, 
               self.ticker, 
               (0 - self.cash) / 100, 
               self.currentValue() / 100,
               ((self.number * self.price) + self.cash) / 100)
    
    def activeCost(self):
        cost = 0
        for purchase in self.activePurchases():
            cost += purchase.size()
        return cost
        
    def activeProfit(self):
        profit = 0
        for purchase in self.activePurchases():
            profit += purchase.absolute_profit()
        return profit
    
    def profit(self):
        return self.currentValue() + self.cash
    
    def toStringActive(self):
        return "%8d %6s, cost \N{pound sign}%8.2f, value = \N{pound sign}%8.2f, profit = \N{pound sign}%8.2f"%(\
               self.number, 
               self.ticker, 
               self.activeCost() / 100, 
               self.currentValue() / 100,
               self.activeProfit() / 100)
        
    def totalDividends(self):
        dividends = 0
        for purchase in self.activePurchases():
            dividends += purchase.total_dividends()
        return dividends
        
    def perShareDividends(self, active = False):
        dividends = 0
        number = 0
        if active:
            purchaseList = self.activePurchases()
        else:
            purchaseList = self.purchases
        for purchase in purchaseList:        
            dividends += purchase.dividends_received * purchase.number_left()
            number += purchase.number_left()
        return dividends / number
                
    def averagePurchasePrice(self):
        numerator = 0
        denominator = 0        
        for purchase in self.activePurchases():        
            numerator += purchase.number_left() * purchase.purchase_price
            denominator += purchase.number_left()
        return numerator / denominator        
                
    def capitalGain(self):
        return self.profit() - self.totalDividends()
        
    def averageHoldingPeriod(self):
        numerator = 0
        denominator = 0        
        for purchase in self.activePurchases():        
            numerator += purchase.number_left() * purchase.holdingPeriod()
            denominator += purchase.number_left()
        if denominator == 0:
            return(0)
        else:
            return numerator / denominator
        
    def maxHoldingPeriod(self):
        maxPeriod = 0
        for purchase in self.activePurchases():        
            maxPeriod = max(maxPeriod, purchase.holdingPeriod())
        return maxPeriod
        
    def firstBought(self):
        first = None
        for purchase in self.activePurchases():
            if not first or purchase.date_bought < first:
                first = purchase.date_bought
        return first
        
    def boughtDates(self):
        list = []
        for purchase in self.purchases:
            list.append(purchase.date_bought)
        return list
        
    def activeBoughtDates(self):
        list = []
        for purchase in self.activePurchases():
            list.append(purchase.date_bought)
        return list
                
