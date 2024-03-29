from .transaction import transaction
from datetime import datetime

class purchase:

    def __init__(self,
                 share,
                 number,
                 date_bought,
                 purchase_price = 0.0,
                 date_sold = None,
                 sale_price = 0.0,
                 value_now = 0.0,
                 dividends_received = 0.0):
        self.share = share
        self.number = number
        self.number_sold = 0
        self.date_bought = date_bought
        if date_sold:
            self.date_sold = date_sold
        else:
            self.date_sold = []
        self.purchase_price = purchase_price
        self.sale_price = sale_price
        self.value_now = value_now
        self.dividends_received = dividends_received
        self.ticker = share

    def size(self):
        return self.number * self.purchase_price
        
    def dividend(self, number, divi):
        if self.number_left():
            self.dividends_received += divi * (min(number, self.number_left()) / (self.number_left()))
        number -= min(number, self.number_left())
        return number

    def scrip(self, scrip):
        self.number *= 1 + scrip
        
    def number_left(self):
        return (self.number - self.number_sold)

    def sell(self, number, price, date):
        if number > 0.1 and self.number_left() > 0.1:
            #print "Sell:", self.ticker, self.date_sold, date
            self.date_sold.append(date)
            self.sale_price = (self.sale_price * self.number_sold + min(number, self.number_left()) * price) / (self.number_sold + min(number, self.number_left()))
            self.number_sold += min(number, (self.number_left()))
            number -= min(number, self.number_left())
        return number

    def note_price(self, price):
        self.value_now = price

    def percent_profit(self):
        return (((self.closing_price() + self.dividends_received) - self.purchase_price) * 100) / self.purchase_price

    def absolute_profit(self):
        return self.percent_profit() * self.size() / 100 
        
    def annual_profit(self):
        return 100 * ((1 + (self.percent_profit() / 100)) ** (365.0 / self.holdingPeriod()) - 1)    
        
    def uniqueId(self):
        return "%s-%s"%(self.ticker, self.date_bought)
        
    def value(self):
        return self.closing_price() * self.number 
        
    def total_dividends(self):
        return self.dividends_received * self.number
        
    def verb(self):
        if self.number_sold > 0:
            if self.number_left() > 0.1:
                verb = "sold/now"
            else:
                verb = "sold"
        else:
            verb = "now"
        return verb

    def credit_rights(self, dilution, price):
        self.purchase_price = (self.purchase_price * self.number + self.number * dilution * price) / (self.number * (1 + dilution))
        self.number = self.number_left() * (1 + dilution) + self.number_sold
        
    def closing_price(self):
        if self.number_sold > 0.1:
            if self.number_left() > 0.1:
                price = (self.number_left() * self.value_now + self.number_sold * self.sale_price) / self.number
            else:
                price = self.sale_price
        else:
            price = self.value_now
        return price

    def toString(self):
        return "%6.2f%% %6s Bought @ %9.2f %12s %9.2f earned %6.2f"%(\
               self.percent_profit(), 
               self.share, 
               self.purchase_price, 
               self.verb(), 
               self.closing_price(), 
               self.dividends_received)
        
    def capitalGain(self):
        return (self.closing_price() - self.purchase_price) * self.number_left()
        
    def holdingPeriod(self):
        if self.number_left() > 0:
            holdingPeriod = (datetime.today().date() - self.date_bought).days
        else:
            holdingPeriod = (max(self.date_sold) - self.date_bought).days
        return holdingPeriod