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
    def fixRawPrice(ticker, price, priceDate, prices):
        if ticker.find("SLXX") != -1:
            price *= 100
        if ticker.find("CPT") != -1:
            price *= 100
        if ticker.find("IS15") != -1 and price < 1000:
            price *= 100
        if ticker.find("BRK-B") != -1:
            price *= 100.0 / prices[("USD", priceDate)]
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
            price = Price.fixRawPrice(ticker, price, datetime.date.today(), prices)
            prices[(ticker, datetime.date.today())] = price
        
        return prices

    @staticmethod        
    def getCurrencyHistory(currency, startDate, prices, urlCache, urls):
        for url in urls:
            html = urlCache.read_url(url)
            for rate in EXCHANGE.findall(html):
                currencyDate = datetime.date(int(rate[2]), int(rate[0]), int(rate[1]))
                prices[(currency, currencyDate)] = float(rate[3])
                
    # Create a price
    def __init__(self, name, date, price):
        self.name = name
        self.date = date
        self.price = price
