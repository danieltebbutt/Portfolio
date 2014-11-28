# A holding is an individual shareholding

from transaction import transaction

class Holding:

    def __init__(self, ticker):
        self.ticker = ticker
        self.number = 0
        self.cash = 0

    def applyTransaction(self, transaction):
        (self.number, self.cash) = transaction.applyTransaction(self.number, self.cash)

    def toString(self):
        return u"%8d %6s, net cost \N{pound sign}%8.2f"%(self.number, self.ticker, (0 - self.cash) / 100)
