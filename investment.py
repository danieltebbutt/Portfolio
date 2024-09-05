#
# Information relevant to a particular investment (stock, bond, currency)
#

import datetime
import re
import os

# A line from stocks.txt
STOCK=re.compile('(?P<stock>[\w^.-]+),\s+(?P<sector>[\w\d.]+),\s+'\
                 '(?P<class>[\w\d.]+),\s+(?P<region>[\w\d.]+),\s+(?P<size>[\w\d.]+),\s+(?P<estdivi>[\d.]+),\s+(?P<isin>[\w\d-]+),\s+(?P<name>[\d\w. \%<>\"=\/\&\[\]\:\=\?\+-]+)\s*\n')
FULLNAME=re.compile('<A HREF="(?P<url>[\d\w.\%=\/\&\[\]\:\=\?\+]+)">(?P<name>[\d\w. \%\"=\/\&\[\]\:\=\?\+-]+)</A>')

filename = os.path.normpath("./data/stocks.csv")

class investment:

    @staticmethod
    def learn_investments(transactions, inputStream = None):
        investments = {}

        if not inputStream:
            inputStream = open(filename)

        for line in inputStream:
            parsedline = STOCK.match(line)
            if parsedline != None:
                stock=parsedline.group('stock')
                sector=parsedline.group('sector')
                assetclass=parsedline.group('class')
                size=parsedline.group('size')
                region=parsedline.group('region')
                estdivi=float(parsedline.group('estdivi'))
                isin=parsedline.group('isin')
                name=parsedline.group('name')
                earliest_date = datetime.date(year = 2050, month = 1, day = 1)
                for transaction in transactions:
                    if transaction.date < earliest_date:
                        earliest_date = transaction.date
                    if transaction.stock not in investments and (transaction.stock == stock):
                        investments[transaction.stock] = investment(stock,
                                                                    sector,
                                                                    assetclass,
                                                                    size,
                                                                    region,
                                                                    transaction.date,
                                                                    estdivi,
                                                                    isin,
                                                                    name)
                
                # Some currencies are tracked even if we never record any buys or sells               
                if stock not in investments and assetclass == "Currency":
                    investments[stock] = investment(stock,
                                                    sector,
                                                    assetclass,
                                                    size,
                                                    region,
                                                    earliest_date,
                                                    estdivi,
                                                    isin,
                                                    name)
        # Check everything is listed in stocks.csv
        for transaction in transactions:
            if transaction.stock not in investments:
                print("Investment not found in stocks.csv, or line malformed: %s"%transaction.stock)
                exit(-1)
        return investments

    # Create this investment type
    def __init__(self, name, sector, assetclass, size, region, first_purchased, estdivi, isin, fullname):
        self.name = name
        self.sector = sector
        self.assetclass = assetclass
        self.size = size
        self.region = region
        self.first_purchased = first_purchased
        self.estdivi = estdivi
        self.isin = isin
        parsedName = FULLNAME.match(fullname)
        if parsedName:
            self.fullname = parsedName.group('name')
            self.blogUrl = parsedName.group('url')
        else:
            self.fullname = fullname
            self.blogUrl = None

    def history_url(self, start_date, last_date):
        urls = []
        if self.first_purchased >= start_date:
            start_date = self.first_purchased
        if self.assetclass != "Currency":
            urls.append("http://ichart.finance.yahoo.com/table.csv?s=%s&a=%d&b=%d&c=%d&d=%d&e=%d&f=%d&g=d&ignore=.csv" \
                % (self.name, start_date.month-1, start_date.day, start_date.year, \
                   last_date.month-1, last_date.day, last_date.year))
        else:
            while start_date < last_date:
                if (last_date - start_date) > datetime.timedelta(days=490):
                    next_date = start_date + datetime.timedelta(days=490)
                else:
                    next_date = last_date
                if self.name == "USD":
                    urls.append("http://www.oanda.com/convert/fxhistory?date_fmt=us&date=%d/%d/%d&date1=%d/%d/%d&exch=GBP&expr=USD&lang=en&margin_fixed=0&format=CSV&redirected=1"\
                        % (next_date.month, next_date.day, (next_date.year%100), \
                        start_date.month, start_date.day, (start_date.year%100)))
                elif self.name == "Euro":
                    urls.append("http://www.oanda.com/convert/fxhistory?date_fmt=us&date=%d/%d/%d&date1=%d/%d/%d&exch=GBP&expr=EUR&lang=en&margin_fixed=0&format=CSV&redirected=1"\
                        % (next_date.month, next_date.day, (next_date.year%100), \
                        start_date.month, start_date.day, (start_date.year%100)))
                elif self.name == "NOK":
                    urls.append("http://www.oanda.com/convert/fxhistory?date_fmt=us&date=%d/%d/%d&date1=%d/%d/%d&exch=GBP&expr=NOK&lang=en&margin_fixed=0&format=CSV&redirected=1"\
                        % (next_date.month, next_date.day, (next_date.year%100), \
                        start_date.month, start_date.day, (start_date.year%100)))
                start_date = next_date

        return urls

    def description(self):
        if self.assetclass == "Currency":
            desc = self.name
        elif self.assetclass == "Bonds":
            desc = "%s %s"%(self.region, self.assetclass)
        else:
            desc = "%s %s"%(self.region, self.assetclass)
        return desc

    def print_diags(self):
        print(self.history_url(datetime.date(year=2008,month=1,day=1), datetime.date(year=2010,month=1,day=1)))
