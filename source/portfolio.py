# The main portfolio class

import re
import datetime
import operator
import math
import ftplib
import webbrowser

import publish
from investment import investment
from transaction import transaction
from day import day
from urlcache import urlcache
from purchase import purchase
from trace import trace

# A line from tracking.txt
TRACK=re.compile('(?P<stock>[\w.]+)\s+(?P<dtvalue>[\d.]+)\s.*')

# A line from Yahoo (portfolio)
YAHOODAY=re.compile('(?P<date>[\d-]+),(?P<open>[\d.]+),(?P<high>[\d.]+),(?P<low>[\d.]+),'\
                    '(?P<close>[\d.]+),(?P<volume>[\d.]+),(?P<adjclose>[\d.]+)')

# A line from Yahoo (tracking)
YAHOOSTOCK=re.compile('\"(?P<stock>[\w.-]+)\",(?P<price>[\d.]+)[, +-/\d:PAM]*')

# A date in Yahoo format
YAHOODATE=re.compile('(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)')

# A line from oanda.com's exchange rate history
EXCHANGE=re.compile('(?P<month>\d+)/(?P<day>\d+)/(?P<year>\d+),(?P<rate>[\d.]+)')

# A line from OtherAssets.txt
OTHERASSET=re.compile('(?P<name>[\w.-_]+)\s+(?P<type>\w+)\s+(?P<value>[\d.-]+)\s+(?P<date>\d+/\d+/\d+)\s+(?P<change>[\d.]+)\s*\n')

# A line from save.csv
TEXTSAVE=re.compile('(?P<stock>[\w.-]+),(?P<year>[\d]+)-(?P<month>[\d]+)-(?P<day>[\d]+),(?P<price>[\d.]+)')

LATEST_PRICES_URL="http://download.finance.yahoo.com/d/quotes.csv?s=%s&f=sl1d1t1c1ohgv&e=.csv"
ROK_BANKRUPT=datetime.date(year=2010,month=11,day=8)
CPT_REDENOMINATED=datetime.date(year=2009,month=7,day=28)

dollar_sign=u'\N{dollar sign}'
pound_sign=u'\N{pound sign}'
errors=[]


class portfolio:

    def __init__(self, verbose = False, text_mode = False):
        # Gather data
        self.history = None
        self.verbose = verbose
        self.gather_data(datetime.date(year = 2008, month = 1, day = 1), text_mode = text_mode)

    def text_save(self):
        # Open the output file ready for writing
        outputfile = open ( '.\\data\\save.csv', 'w')
        shares = []
        keys = self.history.keys()
        keys.sort()
        for day in keys:
            for share in self.history[day].shares:
                if share not in shares:
                    shares.append(share)
        for share in shares:
            for date in sorted(self.history):
                day = self.history[date]
                if day.share_held(share):
                    outputfile.write("%s,%s,%s\n"%(share,date,day.get_price(share)))
        outputfile.close()

    def text_load(self):
        self.gather_data(datetime.date(year = 2008, month = 1, day = 1), text_mode=True)

    def today(self):
        keys = self.history.keys()
        keys.sort()
        return keys[-1]

    def first_day(self):
        keys = self.history.keys()
        keys.sort()
        return keys[0]

    def update(self):
        # The last few days of data could be unreliable
        self.gather_data(datetime.date.today() - datetime.timedelta(days=30))

    def gather_data(self, start_date, text_mode = False):
        if self.verbose:
            print "Reading trackers..."
        self.trackstring,self.trackers = self.read_trackers()
        if self.verbose:
            print "Reading transactions..."
        self.transactions = self.read_transactions()
        if self.verbose:
            print "Creating history..."
        self.create_history(start_date)
        if self.verbose:
            print "Learning investments..."
        self.investments = investment.learn_investments(self.transactions)

        urls=[]
        for item in self.investments:
            if self.investments[item].assetclass == "Currency":
                today = datetime.date.today()
            else:
                today = datetime.date.today() - datetime.timedelta(days=1)
            urls = urls + self.investments[item].history_url(start_date, today)

        self.portfolio_string=""
        for stock in self.investments:
            if self.investments[stock].assetclass != "Currency":
                self.portfolio_string="%s%s+"%(self.portfolio_string, self.investments[stock].name)

        # Get the latest prices.
        url=LATEST_PRICES_URL%self.portfolio_string

        urls.append(url)

        self.urlcache = urlcache(urls)
        self.urlcache.cache_urls()

        if self.verbose:
            print "Getting currency rates..."
        self.get_currency_rates("USD", start_date)
        self.get_currency_rates("Euro", start_date)
        self.get_currency_rates("NOK", start_date)
        if self.verbose:
            print "Getting price history..."
        self.get_price_history(start_date, text_mode)
        if not text_mode:
            if self.verbose:
                print "Getting latest prices..."
            self.get_latest_prices()
        if self.verbose:
            print "Fixing price history gaps..."
        self.fix_price_history_gaps()
        if self.verbose:
            print "Breaking down investments..."
        self.sectors, self.sizes, self.regions, self.assetclasses, self.descriptions = self.breakdown_investments()
        if self.verbose:
            print "Getting purchases..."
        #get_kroner_rates(investments)
        self.purchases = self.get_purchases()
        if self.verbose:
            print "Complete"
        self.urlcache.clean_urls()

    def reparse(self):
        self.investments = self.learn_investments()
        self.sectors, self.sizes, self.regions, self.assetclasses, self.descriptions = self.breakdown_investments()
        self.purchases = self.get_purchases()

    def update_tracking(self):
        self.trackstring,self.trackers = self.read_trackers()

    # Read the list of stocks to track from tracking.txt
    def read_trackers(self):
        trackers = {}
        trackstring = ""
        for line in open(".\\data\\tracking.txt"):
            parsedline = TRACK.match(line)
            if parsedline != None:
                stock=parsedline.group('stock')
                dtvalue=float(parsedline.group('dtvalue'))
                trackers[stock] = dtvalue
                trackstring="%s%s,"%(trackstring,stock)
        return trackstring, trackers

    # Read the transaction history from portfolio.txt
    def read_transactions(self):
        transactions = []
        for line in open(".\\data\\portfolio.txt"):
            if transaction.valid(line):
                tran = transaction(line)
                if tran.date <= datetime.date.today():
                    transactions.append(tran)
        return transactions

    # Add up all transaction expenses
    def expenses(self):
        expenses = 0
        for transaction in self.transactions:
            expenses += transaction.comm
        return expenses

    # Parse all transactions into a portfolio history
    def create_history(self, start_date):
        if self.history == None:
            self.history = {}
            start_date = self.transactions[0].date
            current_day = day(start_date)
        else:
            current_day = self.history[start_date - datetime.timedelta(days=1)].nextday()
        self.history[current_day.date] = current_day
        for transaction in self.transactions:
            # Bring our history up to date
            if transaction.date >= current_day.date:
                while current_day.date < transaction.date:
                    current_day = current_day.nextday()
                    self.history[current_day.date] = current_day

                # Apply this transaction to the current day
                transaction.apply(current_day)
            elif transaction.date >= start_date:
                print "ERROR READING TRANSACTIONS: DATES OUT OF ORDER:"
                print transaction.toString()
                errors.append("DATE ERROR %s"%transaction.toString())

        # Move up to the present day
        while current_day.date < datetime.date.today():
            current_day = current_day.nextday()
            self.history[current_day.date] = current_day

    # Get details on all individual investment types
    # Read latest prices for all shares in the portfolio
    def get_latest_prices(self):
        # Get the latest prices.
        url=LATEST_PRICES_URL%self.portfolio_string

        html = self.urlcache.read_url(url)
        for stockdata in YAHOOSTOCK.findall(html):
            stock = stockdata[0]
            price = float(stockdata[1])
            if stock.find("SLXX") != -1:
                price *= 100
            #if stock.find("LLPF") != -1:
            #    price *= 100
            if stock.find("CPT") != -1:
                price *= 100
            if stock.find("IS15") != -1 and price < 1000:
                price *= 100
            self.history[datetime.date.today()].note_price(stock, price)

    # For each investment, get its price history
    def get_price_history(self, start_date, text_mode):
        if not text_mode:
            url = ""
            pools={}
            pool=0
            for stock in self.investments.keys():
                stockdate = self.investments[stock].first_purchased
                if start_date > stockdate:
                    stockdate = start_date
                if self.investments[stock].assetclass != "Currency":
                    url = self.investments[stock].history_url(start_date, datetime.date.today() - datetime.timedelta(days=1))[0]
                    html = self.urlcache.read_url(url)
                    for daysdata in YAHOODAY.findall(html):
                        date=daysdata[0]
                        closeprice=float(daysdata[4])
                        stockdate = datetime.date(int(YAHOODATE.match(date).group('year')), \
                                                  int(YAHOODATE.match(date).group('month')), \
                                                  int(YAHOODATE.match(date).group('day')))
                        if stock.find("IS15") == -1:
                            if stock.find("RBS") != -1:
                                closeprice = closeprice / 100;
                            self.history[stockdate].note_price(stock, closeprice)
        else:
            for line in open(".\\data\\save.csv"):
                parsedline = TEXTSAVE.match(line)
                if parsedline != None:
                    stock=parsedline.group('stock')
                    price=float(parsedline.group('price'))
                    date=datetime.date(int(parsedline.group('year')), \
                                       int(parsedline.group('month')), \
                                       int(parsedline.group('day')))
                    self.history[date].note_real_price(stock, price)

    def fix_price_history_gaps(self):
        day = None
        keys = self.history.keys()
        keys.sort()
        for date in keys:
            previous_day = day
            day = self.history[date]
            for index, stock in day.shares.iteritems():
                if not stock.price_set and previous_day != None and previous_day.shares.has_key(stock.stock):
                    stock.set_price(previous_day.shares[stock.stock].price)
                if stock.stock == "ROK.L" and date >= ROK_BANKRUPT:
                    stock.set_price(0)

    # Get the history of the dollar/sterling exchange rate
    def get_currency_rates(self, currency, start_date):
        latest_date = datetime.date.today()
        urls = self.investments[currency].history_url(start_date, datetime.date.today())
        for url in urls:
            html = self.urlcache.read_url(url)
            for rate in EXCHANGE.findall(html):
                stockdate = datetime.date(int(rate[2]), int(rate[0]), int(rate[1]))
                self.history[stockdate].note_price(currency, float(rate[3]))

    # def get_kroner_rates
    # Get kroner as well
    #print "Kroner"
    #kroner_history = {}
    #url="http://www.oanda.com/convert/fxhistory?date_fmt=us&date=%d/%d/%d&date1=%d/%d/%d&exch=GBP&expr=NOK&lang=en&margin_fixed=0&format=CSV&redirected=1"%(time.localtime().tm_mon, time.localtime().tm_mday, (time.localtime().tm_year%100), datestart.month, datestart.day, (datestart.year%100))
    #response = urllib2.urlopen(url)
    #html = response.read()
    #for rate in EXCHANGE.findall(html):
    #    stockdate = datetime.date(int(rate[2]), int(rate[0]), int(rate[1]))
    #    kroner_history[stockdate] = float(rate[3])


    # Break down the list of investments by sector, size, region and asset class
    def breakdown_investments(self):
        sectors = []
        sizes = []
        regions = []
        assetclasses = []
        descriptions = []
        for index,investment in self.investments.iteritems():
            if not investment.sector in sectors:
                sectors.append(investment.sector)
            if not investment.size in sizes:
                sizes.append(investment.size)
            if not investment.region in regions:
                regions.append(investment.region)
            if not investment.assetclass in assetclasses:
                assetclasses.append(investment.assetclass)
            if not investment.description() in descriptions:
                descriptions.append(investment.description())
        return (sectors, sizes, regions, assetclasses, descriptions)

    # How much is invested in a particular sector
    def sector_invested(self, sector, today):
        total = 0.0
        for index, investment in self.investments.iteritems():
            if investment.sector == sector:
                total += today.share_invested(investment.name)
        return total

    # How much is invested in companies of a particular size
    def size_invested(self, investments, size, today):
        total = 0.0
        for index, investment in investments.iteritems():
            if investment.size == size:
                total += today.share_invested(investment.name)
        return total

    # How much is invested in a particular region
    def region_invested(self, investments, region, today):
        total = 0.0
        for index, investment in investments.iteritems():
            if investment.region == region:
                total += today.share_invested(investment.name)
        return total

    # How much is invested in a particular asset class
    def assetclass_invested(self, investments, assetclass, today):
        total = 0.0
        for index, investment in investments.iteritems():
            if investment.assetclass == assetclass:
                total += today.share_invested(investment.name)
        return total

    # How much is invested in investments with a particular description
    def description_invested(self, desc, today):
        total = 0.0
        for index, investment in self.investments.iteritems():
            if investment.description() == desc:
                total += today.share_invested(investment.name)
        return total

    def get_purchases(self):
        today = self.history[self.last_weekday()]
        purchases = []
        for transaction in self.transactions:
            if transaction.action == "BUY":
                purchases.append(purchase(transaction.stock, transaction.number, transaction.date, transaction.price))
            elif transaction.action in ("INT", "EXDIV"):
                tocredit = transaction.number
                for a_purchase in purchases:
                    if transaction.stock == a_purchase.share:
                        tocredit = a_purchase.dividend(tocredit, transaction.price)
            elif transaction.action == "SELL":
                tocredit = transaction.number
                for a_purchase in purchases:
                    if transaction.stock == a_purchase.share:
                        tocredit = a_purchase.sell(tocredit, transaction.price, transaction.date)
            elif transaction.action == "RIGHTS":
                numheld = 0
                tocredit = transaction.number
                for a_purchase in purchases:
                    if transaction.stock == a_purchase.share:
                        numheld += a_purchase.number_left()
                for a_purchase in purchases:
                    if transaction.stock == a_purchase.share:
                        a_purchase.credit_rights((tocredit / numheld), transaction.price)


        for a_purchase in purchases:
            a_purchase.note_price(today.get_price(a_purchase.share))
        return purchases

    def last_weekday(self):
        weekday = self.today()
        while weekday.weekday() >= 5:
            weekday -= datetime.timedelta(days = 1)
        return weekday

    def fix_date(self, date):
        if date < sorted(self.history)[0]:
            date = sorted(self.history)[0]
        if date > sorted(self.history)[-1]:
            date = sorted(self.history)[-1]
        return date

    def str_to_date(self, str):
        if str.find("/") != -1:
            day, month, year = str.split("/")
        elif str.find("-") != -1:
            day, month, year = str.split("-")
        elif str.find("."):
            day, month, year = str.split(".")
        else:
            print "Unable to recognize date"
            day = 1
            month = 1
            year = 2008

        date = datetime.date(int(year), int(month), int(day))
        date = self.fix_date(date)
        return date

    def load_net_worth(self):
        self.other_assets = []
        for line in open(".\\data\\OtherAssets.txt"):
            parsedline = OTHERASSET.match(line)
            if parsedline != None:
                self.other_assets.append((parsedline.group('name'),
                                          parsedline.group('type'),
                                          parsedline.group('value')))
        self.net_worth = {}
        for asset in self.other_assets:
            if not self.net_worth.has_key(asset[1]):
                self.net_worth[asset[1]] = float(asset[2])
            else:
                self.net_worth[asset[1]] += float(asset[2])

    def match(self):
        exdivs = {}
        for transaction in self.transactions:
            if transaction.action == "EXDIV":
                if not exdivs.has_key(transaction.stock):
                    exdivs[transaction.stock] = 0
                exdivs[transaction.stock] += transaction.price * transaction.number
            if transaction.action == "DIV":
                exdivs[transaction.stock] -= transaction.price * transaction.number

        for index in exdivs:
            if exdivs[index] != 0:
                print "%s = %d"%(index, exdivs[index])


    def publish(self, debugMode = False):
     
        publish.main_page(self)
    
    #
    # PRINTING FUNCTIONS
    #
    def print_tracking_data(self):
        print "Tracking:"
        for index, value in enumerate(self.trackers):
            print "Track %6s: Dan's value %4.fp"%(value,self.trackers[value])
        print

    def print_income(self):
        interest = 0.0
        dividends = 0.0
        print "%-45s %-9s %-9s %-9s"%("Transactions:", "Total:", "Int:", "Divis:")
        for transaction in self.transactions:
            if transaction.action == "EXDIV" or transaction.action == "INT":
                if transaction.action == "EXDIV":
                    dividends += transaction.price * transaction.number / 100
                else:
                    interest += transaction.price * transaction.number / 100
                print "%-45s %s%-8.2f %s%-8.2f %s%-8.2f"%(transaction.description(), pound_sign, interest+dividends, pound_sign, interest, pound_sign, dividends)
        print

    def print_transactions(self):
        print "Transactions:"
        for transaction in self.transactions:
            print transaction.toString()
        print

    def print_latest_prices(self):
        today = self.history[self.today()]
        print "Latest prices:"
        for index, stock in today.shares.iteritems():
            print "%8s %9.2f -- bought %6d at %9.2fp (%.2f%%)"%(stock.stock,
                                                                stock.price,
                                                                stock.number,
                                                                stock.avg_purchase_price,
                                                                100*(stock.price - stock.avg_purchase_price)/stock.avg_purchase_price)
        print

    def print_capital_gains(self):
        today = self.history[self.today()]
        print "Capital gains/losses:"
        print "   Share      Value       Gain"
        shares = []
        gainsum = 0
        losssum = 0
        for index, stock in today.shares.iteritems():
            shares.append((stock.stock,
                           pound_sign,
                           stock.price * stock.number / 100,
                           pound_sign,
                           (stock.price - stock.avg_purchase_price) * stock.number / 100))
        shares.sort(key=operator.itemgetter(4))
        shares.reverse()
        for share in shares:
            print "%8s %s%9.2f %s%9.2f"%share
            if share[4] > 0:
                gainsum += share[4]
            else:
                losssum += share[4]

        print "Cumulative gain = %s%.2f / loss = %s%.2f"%(pound_sign, gainsum, pound_sign, losssum)
        print

    def print_investment_breakdown(self):
        today = self.history[self.today()]
        print "Investment breakdown:"
        sorted_stocks = []
        for index, stock in today.shares.iteritems():
            if stock.stock != 'cash' and stock.number != 0:
                if stock.stock.find(".L") >= 0:
                    printable_stock = stock.stock[:-2]
                else:
                    printable_stock = stock.stock
                sorted_stocks.append((printable_stock,(today.share_invested(stock.stock)*100)/today.total_invested()))
        sorted_stocks.sort(key=operator.itemgetter(1))
        sorted_stocks.reverse()
        for tup in sorted_stocks:
            print "%8s: %.1f%%"%(tup[0],tup[1])
        print

    def print_share_breakdown(self, date, percentage = True,headings=True,currency=False):
        today = self.history[date]

        if currency:
            print "Share breakdown"
        else:
            print "Share breakdown (excluding Currency):"
        total = 0
        shares = []
        for index, share in today.shares.iteritems():
            shares.append((share.stock,today.share_invested(share.stock)))
        shares.sort(key=operator.itemgetter(1))
        shares.reverse()
        if currency:
            total_invested = today.total_invested()
        else:
            total_invested = today.total_invested() - self.sector_invested("Currency", today)

        if headings:
            for sector in self.sectors:
                if (currency or sector != "Currency") and self.sector_invested(sector, today) > 0:
                    if headings:
                        if percentage:
                            print "%20s: %4.1f"%(sector,(self.sector_invested(sector, today)*100)/total_invested)
                        else:
                            print "%15s: %s%.2f"%(sector, pound_sign, self.sector_invested(sector, today)/100)
                    for stock in shares:
                        if self.investments[stock[0]].sector == sector:
                            if percentage:
                                print "%50s: %4.1f"%(stock[0],(stock[1]*100)/total_invested)
                            else:
                                print "%27s: %s%.2f"%(stock[0], pound_sign, stock[1]/100)
                                total += today.share_invested(stock[0])/100
        else:
            for stock in shares:
                if (currency or self.investments[stock[0]].sector != "Currency"):
                    if percentage:
                        print "%50s: %4.1f"%(stock[0],(stock[1]*100)/total_invested)
                    else:
                        print "%27s: %s%.2f"%(stock[0], pound_sign, stock[1]/100)
                        total += today.share_invested(stock[0])/100


        if not percentage:
            print "Total: %s%.2f"%(pound_sign, total)

        print

    def print_portfolio_breakdown(self):
        today = self.history[self.today()]
        print "Portfolio breakdown:"
        portfolio_breakdown=[]
        for desc in self.descriptions:
            portfolio_breakdown.append((desc,(self.description_invested(desc, today)*100)/today.total_invested()))
        print
        portfolio_breakdown.sort(key=operator.itemgetter(1))
        portfolio_breakdown.reverse()
        for item in portfolio_breakdown:
            print "%25s: %4.1f"%item
        print

    def print_size_breakdown(self, sizes, investments, today):
        print "Size breakdown (excluding currency):"
        for size in sizes:
            if size != "NA":
                print "%20s: %4.1f"%(size,(size_invested(investments, size, today)*100)/(today.total_invested() - size_invested(investments, "NA", today)))
        print

    def print_region_breakdown(self, sizes, investments, today):
        print "Region breakdown (including currency):"
        for region in regions:
            print "%20s: %4.1f"%(region,(region_invested(investments, region, today)*100)/today.total_invested())
        print

    def print_class_breakdown(self, sizes, investments, today):
        print "Class breakdown:"
        for assetclass in assetclasses:
            print "%20s: %4.1f"%(assetclass,(assetclass_invested(investments, assetclass, today)*100)/today.total_invested())
        print

    def print_summary(self):
        today = self.history[self.today()]
        yesterday = self.history[self.last_weekday() - datetime.timedelta(days=1)]
        lastweek = self.history[self.last_weekday() - datetime.timedelta(days=7)]
        lastmonth = self.history[self.last_weekday() - datetime.timedelta(days=28)]
        print self.today()
        print "Income/Expenses:"
        print "Interest, dividends:    %s%.2f (of which %s%.2f ex-div)"%(pound_sign, today.earnings/100, pound_sign, today.exdiv / 100)
        print "Taxes and commissions:  %s%.2f"%(pound_sign, self.expenses()/100)
        print
        print "Holdings:"
        print "Shares/Bonds            %s%.2f"%(pound_sign, (today.total_invested() - self.sector_invested("Currency", today))/100)
        if today.shares.has_key("USD"):
            print "Currency                %s%.2f (%s%.2f)"%(pound_sign, self.sector_invested("Currency", today)/100, dollar_sign, self.sector_invested("Currency", today)/today.shares["USD"].price)
        print
        print "Total profit            %s%.2f (Currency %s%.2f, Shares %s%.2f)"%(pound_sign, today.profit()/100,
                                                                                 pound_sign, today.currency_profit()/100,
                                                                                 pound_sign, (today.profit() - today.currency_profit())/100)

        print "Change today            %s%.2f (Currency %s%.2f, Shares %s%.2f)"%(pound_sign, (today.profit() - yesterday.profit())/100,
                                                                                 pound_sign, (today.currency_profit() - yesterday.currency_profit())/100,
                                                                                 pound_sign, (today.profit() - yesterday.profit() - today.currency_profit() + yesterday.currency_profit())/100)

        print "Change this week        %s%.2f (Currency %s%.2f, Shares %s%.2f)"%(pound_sign, (today.profit() - lastweek.profit())/100,
                                                                                 pound_sign, (today.currency_profit() - lastweek.currency_profit())/100,
                                                                                 pound_sign, (today.profit() - lastweek.profit() - today.currency_profit() + lastweek.currency_profit())/100)

        print "Change this month       %s%.2f (Currency %s%.2f, Shares %s%.2f)"%(pound_sign, (today.profit() - lastmonth.profit())/100,
                                                                                 pound_sign, (today.currency_profit() - lastmonth.currency_profit())/100,
                                                                                 pound_sign, (today.profit() - lastmonth.profit() - today.currency_profit() + lastmonth.currency_profit())/100)
        print
        for error in errors:
            print error
            errors.remove(error)

    def print_difference(self, day1, day2, text):
        print text
        changes = []
        total_profit = 0
        total_share_profit = 0
        unrealised_profits = 0
        unrealised_share_profits = 0
        for index, stock in day2.shares.iteritems():
            changes.append((stock.stock,
                           ((day2.share_profit(stock.stock) - day1.share_profit(stock.stock)) * 100) / (day1.share_running_profit(stock.stock) + max(day1.share_book(stock.stock), day2.share_book(stock.stock))),
                           pound_sign,
                           (day2.share_profit(stock.stock) - day1.share_profit(stock.stock)) / 100))
            total_profit += (day2.share_profit(stock.stock) - day1.share_profit(stock.stock)) / 100
            if self.investments[stock.stock].sector != "Currency":
                total_share_profit += (day2.share_profit(stock.stock) - day1.share_profit(stock.stock)) / 100

        for index, stock in day1.shares.iteritems():
            if stock.stock not in day2.shares.keys():
                unrealised_profits += day1.share_profit(stock.stock)
                if self.investments[stock.stock].sector != "Currency":
                    unrealised_share_profits += day1.share_profit(stock.stock)
        changes.sort(key=operator.itemgetter(1))
        changes.reverse()
        for change in changes:
            print "%6s %5.2f%% (%s%.2f)"%change
        print "Investments no longer held: %s%.2f"%(pound_sign, ((day2.unallocated_profit + day2.unallocated_currency_profit - day1.unallocated_profit - day1.unallocated_currency_profit - unrealised_profits) / 100))
        total_profit += ((day2.unallocated_profit + day2.unallocated_currency_profit - day1.unallocated_profit - day1.unallocated_currency_profit - unrealised_profits) / 100)
        total_share_profit += ((day2.unallocated_profit - day1.unallocated_profit - unrealised_share_profits) / 100)
        print "Earnings (included in individual summary): %s%.2f"%(pound_sign, (day2.earnings - day1.earnings) / 100)
        print "Expenses: %s%.2f"%(pound_sign, (day2.expenses - day1.expenses) / 100)
        total_profit -= (day2.expenses - day1.expenses) / 100
        print "Total profit: %s%.2f"%(pound_sign, total_profit)
        print "Total share profit: %s%.2f"%(pound_sign, total_share_profit)
        #print "  (Profit check: %s%.2f)"%(pound_sign, (day2.profit() - day1.profit()) / 100)
        print
        total_invested = 0
        day_count = 0
        for date in sorted(self.history):
            day = self.history[date]
            if day.date >= day1.date and day.date <= day2.date:
                total_invested += day.raw_share_invested();
                day_count += 1
        average_raw_invested = total_invested / day_count
        basis_for_return = (day1.total_share_invested() - day1.raw_share_invested())+average_raw_invested
        print "Share portfolio:"
        print "Portfolio value at start of period: %s%.2f"%(pound_sign,day1.total_share_invested() / 100)
        print "Portfolio value at end of period: %s%.2f"%(pound_sign,day2.total_share_invested() / 100)
        print "Basis for return accounting for purchase / sale: %s%.2f"%(pound_sign,basis_for_return / 100)
        print "Percentage return on investment: %.2f%%"%(total_share_profit * 10000 / basis_for_return)
        print


    def print_purchases(self):
        ranked_purchases = []
        for purchase in self.purchases:
            ranked_purchases.append((purchase.percent_profit(),
                                     purchase.share,
                                     purchase.purchase_price,
                                     purchase.verb(),
                                     purchase.closing_price(),
                                     purchase.dividends_received))

        ranked_purchases.sort(key=operator.itemgetter(0))
        ranked_purchases.reverse()
        print "Ranked purchases"
        for purchase in ranked_purchases:
            print "%6.2f%% %6s Bought @ %9.2f %12s %9.2f earned %6.2f"%purchase
        print

    def print_purchases_by_size(self):
        ranked_purchases = []
        for purchase in self.purchases:
            ranked_purchases.append((purchase.size() / 100,
                                     purchase.share,
                                     purchase.absolute_profit() / 100,
                                     purchase.verb(),
                                     purchase.value() / 100,
                                     purchase.total_dividends() / 100))

        ranked_purchases.sort(key=operator.itemgetter(0))
        ranked_purchases.reverse()
        print "Ranked purchases"
        for purchase in ranked_purchases:
            print u"\N{pound sign}%9.2f %6s profit \N{pound sign}%9.2f %12s \N{pound sign}%9.2f earned \N{pound sign}%9.2f"%purchase
        print
               
    def print_stats(self):
        total_tradeValue = 0
        num_trades = 0
        comm = 0
        for tran in self.transactions:
            if tran.tradeValue() > 0:
                total_tradeValue += tran.tradeValue()
                num_trades += 1
                comm += tran.comm
        print "Number of trades: %d (average %.1f days between trades)"%(num_trades, ((self.today() - self.first_day()).days)/num_trades)
        print "Average trade value: %s%.2f (tax/commission %s%.2f = %.2f%%)"%(pound_sign, total_tradeValue/(num_trades * 100), pound_sign, comm / (num_trades * 100), (100 * comm) / total_tradeValue)
        year_fraction = (365 / float((self.today() - self.first_day()).days))
        print "Annual turnover: %s%.2f (tax/commission %s%.2f)"%(pound_sign, year_fraction * total_tradeValue / 200, pound_sign, year_fraction * comm / 100)
        print

    def print_all(self):
        today = self.history[self.today()]
        yesterday = self.history[self.last_weekday() - datetime.timedelta(days=1)]
        self.print_tracking_data()
        self.print_transactions()
        self.print_latest_prices()
        self.print_investment_breakdown()
        self.print_share_breakdown(self.today(), True, True, False)
        self.print_portfolio_breakdown()
        self.print_purchases()
        self.print_purchases_by_size()
        self.print_difference(yesterday, today, "Change today:")
        self.print_summary()
        self.print_stats()

    def print_particular_date(self, date1):
        today = self.history[date1]
        self.print_share_breakdown(date1, False, True, False)

    def print_history(self):
        for date in sorted(self.history):
            day = self.history[date]
            day.print_details()

    def print_share_details(self, share):
        for date in sorted(self.history):
            day = self.history[date]
            if day.share_invested(share) != 0:
                print "%s %10d %s @ %10.2fp = %s%10.2f (profit %s%.2f)"%(date,day.share_number(share), share, day.get_price(share), pound_sign, (day.share_invested(share)/100), pound_sign, day.share_profit(share) / 100)

    def print_diags(self):
        self.print_transactions()
        self.print_history()

    def print_months(self):
        day = self.last_weekday() - datetime.timedelta(days=28)
        print "Monthly profit figures:"
        while self.history.has_key(day):
            print "%s -> %s: %s%.2f"%(day,
                                   day + datetime.timedelta(days=28),
                                   pound_sign,
                                   (self.history[day + datetime.timedelta(days=28)].profit() - self.history[day].profit())/100)
            day -= datetime.timedelta(days=28)

    def print_net_worth(self):
        today = self.history[self.today()]
        print "Net worth:"
        print "Shares/Bonds            %s%.2f"%(pound_sign, (today.total_invested() - self.sector_invested("Currency", today))/100)
        if today.shares.has_key("USD"):
            print "Currency                %s%.2f (%s%.2f)"%(pound_sign, self.sector_invested("Currency", today)/100, dollar_sign, self.sector_invested("Currency", today)/today.shares["USD"].price)
        print "Cash                    %s%.2f"%(pound_sign, self.net_worth["CASH"])
        print
        print "Debt                    %s%.2f"%(pound_sign, self.net_worth["LOAN"])
        print
        print "Net current assets      %s%.2f"%(pound_sign, self.net_worth["CASH"] + self.net_worth["LOAN"] + today.total_invested()/100)
        print
        print "Fixed assets            %s%.2f"%(pound_sign, self.net_worth["ASSET"])
        print
        print "Net worth               %s%.2f"%(pound_sign, self.net_worth["CASH"] + self.net_worth["LOAN"] + today.total_invested()/100 + self.net_worth["ASSET"])
        print

    def print_values(self):
        today = self.history[self.last_weekday()]
        print "Valuation:"
        for index, stock in today.shares.iteritems():
            if self.trackers.has_key(stock.stock):
                print "%8s Price %9.2f Value %9.2f (%4.1f%%)"%(stock.stock,
                                                               stock.price,
                                                               self.trackers[stock.stock],
                                                               100*((stock.price - self.trackers[stock.stock])/self.trackers[stock.stock]))
            else:
                print "%8s Price %9.2f Value         ?"%(stock.stock,
                                                         stock.price)
        print

    def print_yield(self):
        today = self.history[self.today()]
        total_cash_dividend = 0
        print "Yield:"
        for index, stock in today.shares.iteritems():
            if self.investments[stock.stock].sector != "Currency":
                print "%6s: %6.1f on %6.0f = %4.1f%%"%(stock.stock,
                                                    self.investments[stock.stock].estdivi,
                                                    today.get_price(stock.stock),
                                                    (self.investments[stock.stock].estdivi * 100) / today.get_price(stock.stock))
                total_cash_dividend += today.shares[stock.stock].number * self.investments[stock.stock].estdivi
        print "Average yield %.1f%%"%(total_cash_dividend * 100 / (today.total_invested() - self.sector_invested("Currency", today)))
        print "Estimated income %s%.0f"%(pound_sign, total_cash_dividend / 100)
        print

    def print_tax(self, year):
        # For all shares held on 1st January after year end, print purchase date, purchase price, number bought, number owned at year end, value at year end. dividend per share received during year
        yearenddate = self.str_to_date("31/12/"+year) + datetime.timedelta(days=1)
        yearbegindate = self.str_to_date("1/1/"+year)
        yearend = self.history[yearenddate]
        yearbegin = self.history[yearbegindate]

        print "____Shares held at year end____"
        div_total_sum=0
        for index, stock in yearend.shares.iteritems():
            print
            print "%s - %s"%(stock.stock, self.investments[stock.stock].isin)
            print "At year end: %d @ %.6f = %.6f NOK"%(yearend.shares[stock.stock].number, yearend.get_price(stock.stock) / yearend.exchange_rates["NOK"], (yearend.shares[stock.stock].number * yearend.get_price(stock.stock) / yearend.exchange_rates["NOK"]))
            print "Transactions:"
            for transaction in self.transactions:
                if transaction.stock == stock.stock and transaction.date < yearenddate:
                    if transaction.action == "BUY" or transaction.action == "SELL" or transaction.action == "RIGHTS" or transaction.action == "SCRIP":
                        print "%s %s %d @ %.6f = %.6f NOK"%(transaction.date, transaction.action, transaction.number, ((transaction.price + (transaction.comm / transaction.number)) / self.history[transaction.date].exchange_rates["NOK"]), (transaction.number * transaction.price + transaction.comm) / self.history[transaction.date].exchange_rates["NOK"])
            print "Dividends:"
            divs=0
            div_share_sum=0
            divs_per_share=0
            for transaction in self.transactions:
                if transaction.stock == stock.stock and transaction.date >= yearbegindate and transaction.date < yearenddate and transaction.action == "DIV":
                    per_share = (transaction.price / self.history[transaction.date].exchange_rates["NOK"])
                    div_total = transaction.number * per_share
                    print "%s %d @ %.6f = %.6f NOK"%(transaction.date, transaction.number, (transaction.price / self.history[transaction.date].exchange_rates["NOK"]), div_total)
                    divs=divs+1
                    div_share_sum = div_share_sum + div_total
                    div_total_sum = div_total_sum + div_total
                    divs_per_share = divs_per_share + per_share
            if divs == 0:
                print "(None)"
            else:
                print " @ %.6f = %.6f NOK"%(divs_per_share, div_share_sum)
        print
        print "Total dividends for the year = %.6f NOK"%div_total_sum


        # For all shares sold during the year, print purchase date, purchase price, number bought, sale date, sale price, number sold, dividend per share received during year
        print
        print "____Shares sold during the year____"
        sold_shares = []
        for transaction in self.transactions:
            if transaction.date < yearenddate and transaction.date > yearbegindate and transaction.action == "SELL" and transaction.stock not in sold_shares:
                sold_shares.append(transaction.stock)
        for stock in sold_shares:
            print
            print "%s - %s"%(stock, self.investments[stock].isin)
            if yearbegin.shares.has_key(stock):
                print "At start of year: %d @ %.6f = %.6f NOK"%(yearbegin.shares[stock].number, yearbegin.get_price(stock) / yearbegin.exchange_rates["NOK"], (yearbegin.shares[stock].number * yearbegin.get_price(stock) / yearbegin.exchange_rates["NOK"]))
            else:
                print "None held at start of year"
            print "Transactions:"
            for transaction in self.transactions:
                if transaction.stock == stock and transaction.date < yearenddate:
                    if transaction.action == "BUY" or transaction.action == "SELL" or transaction.action == "RIGHTS" or transaction.action == "SCRIP":
                        print "%s %s %d @ %.6f = %.6f NOK"%(transaction.date, transaction.action, transaction.number, ((transaction.price + (transaction.comm / transaction.number)) / self.history[transaction.date].exchange_rates["NOK"]), (transaction.number * transaction.price + transaction.comm) / self.history[transaction.date].exchange_rates["NOK"])
            print "Dividends:"
            divs=0
            for transaction in self.transactions:
                if transaction.stock == stock and transaction.date >= yearbegindate and transaction.date < yearenddate and transaction.action == "DIV":
                    print "%s %d @ %.6f = %.6f NOK"%(transaction.date, transaction.number, (transaction.price / self.history[transaction.date].exchange_rates["NOK"]), transaction.number * (transaction.price / self.history[transaction.date].exchange_rates["NOK"]))
                    divs=divs+1
            if divs == 0:
                print "(None)"

    def print_rates(self, rate):
        for date in sorted(self.history):
            print "%s %.2f"%(date, self.history[date].exchange_rates[rate])
