#
# This holds all information relevant to a particular day
#

import datetime

from stockday import stock_day

class day:

    # Create this day
    def __init__(self,
                 date,
                 shares = {},
                 invested = 0.0,
                 raw_invested = 0.0,
                 cash = 0,
                 exdiv = 0,
                 earnings = 0,
                 unallocated_profit = 0,
                 expenses = 0,
                 unallocated_currency_profit = 0,
                 sold_shares = {}):
        self.date = date
        self.shares = shares
        self.invested = invested
        self.raw_invested = raw_invested
        self.cash = cash
        self.exdiv = exdiv
        self.earnings = earnings
        self.unallocated_profit = unallocated_profit
        self.expenses = expenses
        self.exchange_rates = {}
        self.unallocated_currency_profit = unallocated_currency_profit
        self.sold_shares = sold_shares

    def trade_stock(self, stock, number, price, comm):
        self.cash -= number * price + comm
        self.invest((number * price) + comm)
        if not self.shares.has_key(stock):
            self.shares[stock] = stock_day(stock, first_purchase_date = self.date)
        self.shares[stock].trade(number, price)
        if self.shares[stock].number == 0:
            if stock == "USD":
                self.unallocated_currency_profit += self.shares[stock].accumulated_profit + self.shares[stock].accumulated_earnings
            else:
                self.unallocated_profit += self.shares[stock].accumulated_profit + self.shares[stock].accumulated_earnings
            if not self.sold_shares.has_key(stock):
                self.sold_shares[stock] = []
            self.sold_shares[stock].append(self.shares[stock].copy())

            self.sold_shares[stock][-1].price = price
            del self.shares[stock]
        self.expenses += comm

    def ex_dividend(self, stock, number, price):
        self.exdiv += number * price
        self.earnings += number * price
        self.shares[stock].earn(number * price)
        self.raw_invested -= number * price

    def dividend(self, stock, number, price):
        self.exdiv -= number * price
        self.cash += number * price

    def invest(self, amount):
        self.invested += amount
        self.raw_invested += amount

    # Create the next day
    def nextday(self):
        shares_copy = {}
        for share in self.shares:
            shares_copy[share] = self.shares[share].copy()
        sold_shares_copy = {}
        for share in self.sold_shares:
            sold_shares_copy[share] = []
            for dayshare in self.sold_shares[share]:
                sold_shares_copy[share].append(dayshare.copy())
        newday = day(self.date + datetime.timedelta(days=1),
                     shares_copy,
                     self.invested * 1.00013368,
                     self.raw_invested,
                     self.cash,
                     self.exdiv,
                     self.earnings,
                     self.unallocated_profit,
                     self.expenses,
                     self.unallocated_currency_profit,
                     sold_shares_copy)

        return newday

    def note_price(self, stock, price):
        if (stock.find("USD") or stock.find("Euro") or stock.find("NOK")) and price != 0:
            self.exchange_rates[stock] = 100 / price

        if self.shares.has_key(stock):
            if stock.find("USD") != -1:
                # USD per GBP
                self.shares[stock].set_price(100 / price)
            elif stock.find(".L") == -1:
                # Denominated in USD
                self.shares[stock].set_price(price * self.exchange_rates["USD"])
            elif stock.find("CPT.L") != -1 and self.date >= CPT_REDENOMINATED:
                # Carpathian rebased to euros on 28/07/09
                self.shares[stock].set_price(price * self.exchange_rates["Euro"] / 100)
            elif stock.find("ROK.L") != -1 and self.date >= ROK_BANKRUPT:
                # Rok went into administration on 8/11/10
                self.shares[stock].set_price(0)
            else:
                # Denominated in pence
                self.shares[stock].set_price(price)


    def note_real_price(self, stock, price):
        if self.shares.has_key(stock):
            self.shares[stock].set_price(price)

    def total_invested(self):
        total = 0
        for index, share in self.shares.iteritems():
            total += share.number * share.price
        return total

    def share_invested(self, share):
        if self.shares.has_key(share):
            value = (self.shares[share].number * self.shares[share].price)
        else:
            value = 0.0
        return value

    def share_held(self, share):
        if self.shares.has_key(share):
            held = True
        else:
            held = False
        return held

    def total_share_invested(self):
        total = self.total_invested() - self.share_invested("USD")
        return total

    def share_profit(self, share):
        if self.shares.has_key(share):
            value = self.shares[share].profit()
        else:
            value = 0
        return value

    def share_earnings(self):
        earnings = self.earnings
        if self.shares.has_key("USD"):
            earnings -= self.shares["USD"].accumulated_earnings
        elif self.sold_shares.has_key("USD"):
            earnings -= self.sold_shares["USD"][0].accumulated_earnings
        return self.earnings

    def raw_share_invested(self):
        raw_invested = self.raw_invested
        if self.shares.has_key("USD"):
            raw_invested -= self.shares["USD"].book()
        raw_invested += self.unallocated_currency_profit
        return raw_invested

    def currency_profit(self):
        if self.shares.has_key("USD"):
            value = self.shares["USD"].profit()
        else:
            value = 0
        value += self.unallocated_currency_profit
        return value

    def share_running_profit(self, share):
        if self.shares.has_key(share):
            value = self.shares[share].running_profit()
        else:
            value = 0
        return value

    def share_number(self, share):
        if self.shares.has_key(share):
            value = self.shares[share].number
        else:
            value = 0.0
        return value

    def get_price(self, share):
        if self.shares.has_key(share):
            value = self.shares[share].price
        else:
            value = 0.0
        return value

    def profit(self):
        return (self.total_invested() - self.raw_invested)

    def share_book(self, share):
        if self.shares.has_key(share):
            value = self.shares[share].book()
        else:
            value = 0
        return value

    def print_details(self):
        print "%s cash:%.2f raw_inv:%.2f inv:%.2f exdiv:%.2f earnt:%.2f unalloc:%.2f value:%.2f"%(self.date,
                                                                                       self.cash,
                                                                                       self.raw_invested,
                                                                                       self.invested,
                                                                                       self.exdiv,
                                                                                       self.earnings,
                                                                                       self.unallocated_profit,
                                                                                       self.total_invested())
        for index, share in self.shares.iteritems():
            print "  ",
            share.print_details()
