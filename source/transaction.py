#
# A transaction is a purchase or sale of shares, payment of dividend,
# ex-dividend date, scrip issue, rights issue, or similar.
#

import re
import datetime

TRANSACTION=re.compile('(?P<stock>[\w.-]+)\s+(?P<day>\d+)\s+(?P<month>\d+)\s+(?P<year>\d+)\s+'\
                       '(?P<number>[\d.]+)\s+(?P<action>\w+)\s+(?P<price>[\d.]+)\s+(?P<comm>[\d.]+)\s*\n')

dollar_sign=u'\N{dollar sign}'
pound_sign=u'\N{pound sign}'
                       
class transaction:

    #
    # Create a transaction.
    #
    def __init__(self, line):
        parsedline = TRANSACTION.match(line)
        if parsedline == None:
            # Not valid!
            raise Exception('Transaction not valid!')

        #
        # Pull out all the data we want
        #
        self.stock=parsedline.group('stock')
        
        day=int(parsedline.group('day'))
        month=int(parsedline.group('month'))
        year=int(parsedline.group('year'))
        self.date = datetime.date(year, month, day)
        
        self.number=float(parsedline.group('number'))
        self.action=parsedline.group('action')
        self.price=float(parsedline.group('price'))
        self.comm=float(parsedline.group('comm'))

        assert((self.action == "BUY") or
               (self.action == "SELL") or
               (self.action == "RIGHTS") or
               (self.action == "DIV") or
               (self.action == "EXDIV") or
               (self.action == "SCRIP") or
               (self.action == "INT"))

    @staticmethod
    def valid(line):
        return(TRANSACTION.match(line) != None)

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
            return "%s %6s paid interest  of %s%-4.2f"%(self.date.strfime("%d/%m/%y"),
                                                              self.stock,
                                                              pound_sign,
                                                              (self.number * self.price) / 100)
        elif self.action == "EXDIV":
            return "%s %6s paid dividends of %s%-4.2f"%(self.date.strfime("%d/%m/%y"),
                                                              self.stock,
                                                              pound_sign,
                                                              (self.number * self.price) / 100)


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
