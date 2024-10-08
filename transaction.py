#
# A transaction is a purchase or sale of shares, payment of dividend,
# ex-dividend date, scrip issue, rights issue, or similar.
#

import os
import re
import datetime

class transaction:

    TRANSACTION = re.compile(r'(?P<stock>[\w^.-]+)\s+(?P<day>\d+)\s+(?P<month>\d+)\s+(?P<year>\d+)\s+'\
                            r'(?P<number>[\d.]+)\s+(?P<action>\w+)\s+(?P<price>[\d.]+)\s+(?P<comm>[\d.]+)\s*\n')

    ACTIONS = ["BUY", "SELL", "RIGHTS", "DIV", "EXDIV", "SCRIP", "INT"]

    PORTFOLIO_DIR = os.path.normpath("./data")
    PORTFOLIO_NAME = "portfolio.txt"
    portfolio = os.path.normpath("%s/%s"%(PORTFOLIO_DIR, PORTFOLIO_NAME))

    dollar_sign='\N{dollar sign}'
    pound_sign='\N{pound sign}'

    @staticmethod
    def readTransactions(inputFile = None, inputStream = None):

        if not inputStream:
            if inputFile:
                portfolioFile = inputFile
            else:
                portfolioFile = transaction.portfolio

            print(portfolioFile)
            inputStream = open(portfolioFile)

        transactions = []

        for line in inputStream:
            if transaction.valid(line):
                tran = transaction(line)
                #if tran.date <= datetime.date.today():
                transactions.append(tran)
        return sorted(transactions, key=lambda x: x.date)

    @staticmethod
    def writeTransactions(transactionList, outputFile = None, outputStream = None):
        if not outputStream:
            outputStream = open(outputFile, 'w')
        for tran in transactionList:
            transaction.writeTransaction(tran.ticker,
                                         tran.date,
                                         tran.number,
                                         tran.action,
                                         tran.price,
                                         tran.comm,
                                         outputStream = outputStream)

    @staticmethod
    def writeTransaction(ticker, date, number, type, amount, commission, comment = "", outputFile = "", outputStream = None):
        if not outputStream:
            if outputFile:
                portfolioFile = outputFile
            else:
                portfolioFile = portfolio
            outputStream = open(portfolioFile, 'a')

        if comment:
            outputStream.write("# %s"%comment)
        outputStream.write("%-7s %-7d %-7d %-7d %-11f %-11s %-11f %-11f\n"%(
                ticker,
                date.day,
                date.month,
                date.year,
                number,
                type,
                amount,
                commission,
                ))

    @staticmethod
    def dirAndFile():
        return {PORTFOLIO_DIR, PORTFOLIO_NAME}
        
    #
    # Create a transaction.
    #
    def __init__(self, line):
        parsedline = transaction.TRANSACTION.match(line)
        if parsedline == None:
            # Not valid!
            raise Exception('Transaction not valid!')

        #
        # Pull out all the data we want
        #
        self.stock=parsedline.group('stock')
        self.ticker = self.stock

        day=int(parsedline.group('day'))
        month=int(parsedline.group('month'))
        year=int(parsedline.group('year'))
        self.date = datetime.date(year, month, day)

        self.number=float(parsedline.group('number'))
        self.action=parsedline.group('action')
        self.price=float(parsedline.group('price'))
        self.comm=float(parsedline.group('comm'))

        assert(self.action in transaction.ACTIONS)

    @staticmethod
    def valid(line):
        return(transaction.TRANSACTION.match(line) != None)

    def tradeValue(self):
        if (self.action == "BUY" or self.action == "SELL") and self.stock != "USD":
            return self.number * self.price
        else:
            return 0

    # Return a nicely-formatted string of this object
    def toString(self):
        return "%s %6s %6s %9.2f @ %9.2f (comm: %4d)"%(self.date.strftime("%d/%m/%y"),
                                                               self.stock,
                                                               self.action,
                                                               self.number,
                                                               self.price,
                                                               self.comm)

    def description(self):
        if self.action == "INT":
            return "%s %6s paid interest  of %s%-4.2f"%(self.date.strftime("%d/%m/%y"),
                                                              self.stock,
                                                              self.pound_sign,
                                                              (self.number * self.price) / 100)
        elif self.action == "EXDIV":
            return "%s %6s paid dividends of %s%-4.2f"%(self.date.strftime("%d/%m/%y"),
                                                              self.stock,
                                                              self.pound_sign,
                                                              (self.number * self.price) / 100)

    # !!
    def apply(self, day):
        # Apply a transaction to a particular day
        assert (day.date == self.date)

        if self.action == "BUY":
            day.trade_stock(self.stock, self.number, self.price, self.comm)
        elif self.action == "SELL":
            day.trade_stock(self.stock, 0 - self.number, self.price, self.comm)
        elif self.action == "EXDIV":
            day.ex_dividend(self.stock, self.number, self.price)
        elif self.action == "INT":
            day.ex_dividend(self.stock, self.number, self.price)
            day.dividend(self.stock, self.number, self.price)
        elif self.action == "DIV":
            day.dividend(self.stock, self.number, self.price)
        elif self.action == "RIGHTS":
            day.trade_stock(self.stock, self.number, self.price, 0)
        elif self.action == "SCRIP":
            day.trade_stock(self.stock, self.number, 0, 0)
        else:
            raise Exception("Unrecognized field: %s"%self.action)

    def applyTransaction(self, shares, cash):
        if self.action == "BUY":
            shares += self.number
            cash -= self.number * self.price + self.comm
        elif self.action == "SELL":
            shares -= self.number
            cash += self.number * self.price - self.comm
        elif self.action == "EXDIV":
            cash += self.number * self.price
        elif self.action == "INT":
            # !!
            pass
        elif self.action == "DIV":
            # No-op - don't care about actual payment
            pass
        elif self.action == "RIGHTS":
            shares += self.number
            cash -= self.number * self.price + self.comm
        elif self.action == "SCRIP":
            shares += self.number
        else:
            raise Exception("Unrecognized field: %s"%self.action)
        return (shares, cash)

