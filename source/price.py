#
# Price for a particular stock
#

import datetime
import re

# REGULAR EXPRESSIONS

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

# PRICE SOURCES
LATEST_PRICES_URL="http://download.finance.yahoo.com/d/quotes.csv?s=%s&f=sl1d1t1c1ohgv&e=.csv"

# MODIFICATIONS
ROK_BANKRUPT=datetime.date(year=2010,month=11,day=8)
CPT_REDENOMINATED=datetime.date(year=2009,month=7,day=28)

class Price:

    @staticmethod
    def fixRawPrice(ticker, price):
        if ticker.find("SLXX") != -1:
            price *= 100
        if ticker.find("CPT") != -1:
            price *= 100
        if ticker.find("IS15") != -1 and price < 1000:
            price *= 100
        return price
            
    @staticmethod
    def currentPricesUrl(tickerList):
        portfolioString=""
        for ticker in tickerList:
            portfolioString="%s%s+"%(portfolioString, ticker)
        
        url = LATEST_PRICES_URL % portfolioString
        return url
            
    @staticmethod
    def loadCurrentPricesFromWeb(tickerList, prices, urlCache):
        url = Price.currentPricesUrl(tickerList)
        html = urlCache.read_url(url)

        for shareData in YAHOOSTOCK.findall(html):
            ticker = shareData[0]
            price = float(shareData[1])
            price = Price.fixRawPrice(ticker, price)
            prices[(ticker, datetime.date.today())] = price
            print "%s %s %.2f"%(ticker, datetime.date.today(), price)
        
        return prices
        
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

    def loadFromLocalCSV(prices):
        
        
    
        return prices

    # Create a price
    def __init__(self, name, date, price):
        self.name = name
        self.date = date
        self.price = price
