#
# Price for a particular stock
#

import datetime
import re
import operator

# REGULAR EXPRESSIONS

# A line from Yahoo (portfolio)
YAHOODAY=re.compile('(?P<date>[\d-]+),(?P<open>[\d.]+),(?P<high>[\d.]+),(?P<low>[\d.]+),'\
                    '(?P<close>[\d.]+),(?P<volume>[\d.]+),(?P<adjclose>[\d.]+)')

# A line from Yahoo (tracking)
YAHOOSTOCK=re.compile('\"(?P<stock>[\w.-\^]+)\",(?P<price>[\d.]+)[, +-/\d:PAM]*')

# A line from oanda.com's exchange rate history
EXCHANGE=re.compile('(?P<month>\d+)/(?P<day>\d+)/(?P<year>\d+),(?P<rate>[\d.]+)')

# A line from OtherAssets.txt
OTHERASSET=re.compile('(?P<name>[\w.-_]+)\s+(?P<type>\w+)\s+(?P<value>[\d.-]+)\s+(?P<date>\d+/\d+/\d+)\s+(?P<change>[\d.]+)\s*\n')

# save.csv
LOCAL_PRICES = ".\\data\\save.csv"
TEXTSAVE=re.compile('(?P<ticker>[\w.-]+),(?P<year>[\d]+)-(?P<month>[\d]+)-(?P<day>[\d]+),(?P<price>[\d.]+)')

# PRICE SOURCES
LATEST_PRICES_URL = "http://download.finance.yahoo.com/d/quotes.csv?s=%s&f=sl1d1t1c1ohgv&e=.csv"
HISTORICAL_SHARE_PRICE_URL = "http://ichart.finance.yahoo.com/table.csv?s=%s&a=%d&b=%d&c=%d&d=%d&e=%d&f=%d&g=d&ignore=.csv"
HISTORICAL_CURRENCY_PRICE_URL = "http://www.oanda.com/convert/fxhistory?date_fmt=us&date=%d/%d/%d&date1=%d/%d/%d&exch=%s&expr=GBP&lang=en&margin_fixed=0&format=CSV&redirected=1"

# MODIFICATIONS
ROK_BANKRUPT=datetime.date(year=2010,month=11,day=8)
CPT_REDENOMINATED=datetime.date(year=2009,month=7,day=28)

class Price:
    # Methods for fixing problems with the data
    @staticmethod
    def fixRawPrice(ticker, price, priceDate, prices):
        if ticker.find("SLXX") != -1:
            price *= 100
        if ticker.find("CPT") != -1:
            price *= 100
        if ticker.find("IS15") != -1 and price < 1000:
            price *= 100
        if ticker.find("BRK-B") != -1:
            price *= prices[("USD", priceDate)]
        return price

    @staticmethod
    def fixPriceGaps(prices): 
        # Iterate through learning tickers and first and last dates
        # Iterate through filling in gaps
        tickers = []
        dates = {}
        for (ticker, date) in sorted(prices.keys(), key=operator.itemgetter(1)):
            if not ticker in tickers:
                tickers.append(ticker)
                dates[ticker] = [date, date]
            if date < dates[ticker][0]:
                dates[ticker][0] = date
            elif date > dates[ticker][1]:
                dates[ticker][1] = date
        
        for (ticker, date) in sorted(prices.keys(), key=operator.itemgetter(1)):
            while dates[ticker][0] < date - datetime.timedelta(days = 1) and dates[ticker][0] < dates[ticker][1]:
                dates[ticker][0] += datetime.timedelta(days = 1)
                prices[(ticker, dates[ticker][0])] = prices[(ticker, dates[ticker][0] - datetime.timedelta(days = 1))]
            dates[ticker][0] = date

# Methods for building URLs            
    @staticmethod
    def currentPricesUrl(tickerList):
        portfolioString=""
        for ticker in tickerList:
            portfolioString="%s%s+"%(portfolioString, ticker)
        
        url = LATEST_PRICES_URL % portfolioString
        return url

    @staticmethod
    def historicalPricesUrl(ticker, startDate, lastDate, currency = False):
        urls = []
        if not currency:
            urls.append(HISTORICAL_SHARE_PRICE_URL%(
                        ticker, 
                        startDate.month - 1, 
                        startDate.day, 
                        startDate.year,
                        lastDate.month - 1, 
                        lastDate.day, 
                        lastDate.year))
        else:
            while startDate < lastDate:
                # Can't get more than 500 days in one GET from oanda
                if (lastDate - startDate) > datetime.timedelta(days=490):
                    nextDate = startDate + datetime.timedelta(days=490)
                else:
                    nextDate = lastDate
                    
                fixedTicker = "EUR" if ticker == "Euro" else ticker
                urls.append(HISTORICAL_CURRENCY_PRICE_URL%(
                            nextDate.month, 
                            nextDate.day, 
                            (nextDate.year%100),
                            startDate.month, 
                            startDate.day, 
                            (startDate.year%100),
                            fixedTicker))
                startDate = nextDate

        return urls
        
    # Methods for loading and parsing info from the web
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
                price = float(rate[3]) * 100
                prices[(currency, currencyDate)] = price

    @staticmethod                
    def loadHistoricalPricesFromWeb(ticker, startDate, endDate, prices, urlCache):          
        url = Price.historicalPricesUrl(ticker, startDate, endDate, currency = False)[0]
        html = urlCache.read_url(url)
        
        for line in YAHOODAY.findall(html):
            priceDate = datetime.datetime.strptime(line[0], "%Y-%m-%d").date()
            closePrice = float(line[4])
            closePrice = Price.fixRawPrice(ticker, closePrice, priceDate, prices)
            prices[(ticker, priceDate)] = closePrice

    # For each investment, get its price history
    @staticmethod
    def loadHistoricalPricesFromDisk(prices):
        for line in open(LOCAL_PRICES):
            parsedline = TEXTSAVE.match(line)
            if parsedline != None:
                ticker = parsedline.group('ticker')
                price = float(parsedline.group('price'))
                date = datetime.date(int(parsedline.group('year')), \
                                     int(parsedline.group('month')), \
                                     int(parsedline.group('day')))
                prices[(ticker, date)] = price

    @staticmethod
    def writePrices(file, prices, keys):
        for item in keys:
            file.write("%s,%s,%s\n"%(item[0],item[1].strftime("%Y-%m-%d"),prices[item]))    
                
    @staticmethod
    def savePricesToDisk(prices):
        # What are we missing?
        alreadyOnDisk = {}
        Price.loadHistoricalPricesFromDisk(alreadyOnDisk)
        
        with open(LOCAL_PRICES, 'a') as file:
            Price.writePrices(file, prices, set(prices) - set(alreadyOnDisk))
            
    @staticmethod
    def lastDates(prices, tickerList):
        toReturn = {}
        foundAlready = []
        for price in reversed(sorted(prices.keys())):
            if not price[0] in foundAlready:
                foundAlready.append(price[0])
                toReturn[price[0]] = price[1]
        return toReturn

    @staticmethod
    def writeSorted(prices):
        with open(LOCAL_PRICES, 'w') as file:
            Price.writePrices(file, prices, sorted(prices))
        
    # Create a price
    def __init__(self, name, date, price):
        self.name = name
        self.date = date
        self.price = price

        