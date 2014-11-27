import datetime

class stock_day:

    def __init__(self,
                 stock,
                 number = 0,
                 avg_purchase_price = 0,
                 price = 0,
                 purchases = [],
                 accumulated_profit = 0,
                 accumulated_earnings = 0,
                 number_sold = 0,
                 avg_sale_price = 0,
                 raw_invested = 0,
                 first_purchase_date = datetime.date.today(),
                 total_raw_invested = 0,
                 date = None,
                 last_sale_date = None):

        self.stock = stock
        self.number = number
        self.avg_purchase_price = avg_purchase_price
        self.price = price
        self.purchases = purchases
        self.price_set = False
        self.accumulated_profit = accumulated_profit
        self.accumulated_earnings = accumulated_earnings
        self.number_sold = number_sold
        self.avg_sale_price = avg_sale_price
        self.trade_price = 0
        self.raw_invested = raw_invested
        self.first_purchase_date = first_purchase_date
        self.total_raw_invested = total_raw_invested
        if date == None:
            self.date = first_purchase_date
        else:
            self.date = date
        if last_sale_date == None:
            self.last_sale_date = None
        else:
            self.last_sale_date = last_sale_date

    def trade(self, number, price):
        self.trade_price = price
        if number > 0:
            self.avg_purchase_price *= self.number
            self.avg_purchase_price += number * price
        self.number += number
        if self.number != 0 and number > 0:
            self.avg_purchase_price /= self.number
        if self.price == 0:
            self.price = price
        if number < 0:
            self.accumulated_profit -= number * (price - self.avg_purchase_price)
            self.avg_sale_price *= self.number_sold
            self.avg_sale_price -= number * price
            self.number_sold -= number
            self.avg_sale_price /= self.number_sold
        self.raw_invested += number * price
        if self.number < 0.1:
            self.last_sale_date = self.date

    def set_price(self, price):
        self.price = price
        self.price_set = True
        if self.trade_price != 0 and (self.trade_price > price * 1.1 or self.trade_price < price * 0.9):
            print "Possible data error: %s, quoted at %.2f, traded at %.2f"%(self.stock, self.price, self.trade_price)

    def earn(self, earnings):
        self.accumulated_earnings += earnings
        self.raw_invested -= earnings

    def copy(self):
        new_stock_day = stock_day(self.stock,
                                  self.number,
                                  self.avg_purchase_price,
                                  self.price,
                                  self.purchases,
                                  self.accumulated_profit,
                                  self.accumulated_earnings,
                                  self.number_sold,
                                  self.avg_sale_price,
                                  self.raw_invested,
                                  self.first_purchase_date,
                                  (self.total_raw_invested + self.raw_invested) if (self.last_sale_date == None) else self.total_raw_invested,
                                  self.date + datetime.timedelta(days=1),
                                  self.last_sale_date)

        return new_stock_day

    def print_details(self):
        print "%s %.0f @ %.2fp now %.2f.  Profit=%.2f Book=%.2f Value=%.2f"%(self.stock, self.number, self.avg_purchase_price, self.price, self.profit(), self.book(), self.number*self.price)

    def profit(self):
        prof = self.number * (self.price - self.avg_purchase_price) + self.accumulated_profit + self.accumulated_earnings
        return prof

    def running_profit(self):
        prof = self.number * (self.price - self.avg_purchase_price) + self.accumulated_earnings
        return prof

    def book(self):
        value = self.number * self.avg_purchase_price
        return value

    def avg_raw_invested(self):
        if datetime.date.today() == self.first_purchase_date:
            return 0
        elif self.last_sale_date == None:
            return self.total_raw_invested / ((datetime.date.today() - self.first_purchase_date).days)
        else:
            return self.total_raw_invested / ((self.last_sale_date - self.first_purchase_date).days)

    def holding_period(self):
        if self.last_sale_date != None:
            return (self.last_sale_date - self.first_purchase_date).days
        else:
            return (self.date - self.first_purchase_date).days
