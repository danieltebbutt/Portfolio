class purchase:

    def __init__(self,
                 share,
                 number,
                 date_bought,
                 purchase_price = 0.0,
                 date_sold = [],
                 sale_price = 0.0,
                 value_now = 0.0,
                 dividends_received = 0.0):
        self.share = share
        self.number = number
        self.number_sold = 0
        self.date_bought = date_bought
        self.date_sold = date_sold
        self.purchase_price = purchase_price
        self.sale_price = sale_price
        self.value_now = value_now
        self.dividends_received = dividends_received

    def size(self):
        return self.number * self.purchase_price
        
    def dividend(self, number, divi):
        self.dividends_received += divi * (min(number, self.number) / self.number)
        number -= min(number, self.number)
        return number

    def number_left(self):
        return (self.number - self.number_sold)

    def sell(self, number, price, date):
        if self.share == "GNK.L":
            print "%.2f, %.2f, %s"%(number, price, date)
        if number > 0.1 and self.number_left() > 0.1:
            self.date_sold.append(date)
            self.sale_price = (self.sale_price * self.number_sold + min(number, self.number_left()) * price) / (self.number_sold + min(number, self.number_left()))
            self.number_sold += min(number, (self.number_left()))
            number -= min(number, self.number)
        return number

    def note_price(self, price):
        self.value_now = price

    def percent_profit(self):
        return (((self.closing_price() + self.dividends_received) - self.purchase_price) * 100) / self.purchase_price

    def absolute_profit(self):
        return self.percent_profit() * self.size() / 100 
        
    def value(self):
        return self.closing_price() * self.number 
        
    def total_dividends(self):
        return self.dividends_received * self.number
        
    def verb(self):
        if self.number_sold > 0:
            if self.number_left() > 0.1:
                verb = "sold/now"
                print "%.2f, %.2f"%(self.number_sold, self.number_left())

            else:
                verb = "sold"
        else:
            verb = "now"
        return verb

    def credit_rights(self, dilution, price):
        self.purchase_price = (self.purchase_price * self.number + self.number * dilution * price) / (self.number * (1 + dilution))
        self.number *= (1 + dilution)

    def closing_price(self):
        if self.number_sold > 0.1:
            if self.number_left() > 0.1:
                price = (self.number_left() * self.value_now + self.number_sold * self.sale_price) / self.number
            else:
                price = self.sale_price
        else:
            price = self.value_now
        return price
