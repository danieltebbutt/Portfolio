#
# Price for a particular stock
#

import os
import datetime
import re
import operator
from forex_python.converter import CurrencyRates
import json
import sys, traceback

# REGULAR EXPRESSIONS

# A line from Yahoo (portfolio)
#YAHOODAY=re.compile('(?P<date>[\d-]+),(?P<open>[\d.]+),(?P<high>[\d.]+),(?P<low>[\d.]+),'\
#                    '(?P<close>[\d.]+),(?P<volume>[\d.]+),(?P<adjclose>[\d.]+)')

YAHOODAY=re.compile('(?P<date>\d+-[A-Z][a-z][a-z]-\d+),(?P<open>[\d.]+),(?P<high>[\d.]+),(?P<low>[\d.]+),'\
                    '(?P<close>[\d.]+),(?P<volume>[\d.]+)')

# A line from Yahoo (tracking)
YAHOOSTOCK=re.compile('\"(?P<stock>[\w^.-]+)\",(?P<price>[\d.]+)[, +-/\d:PAM]*')

# A line from oanda.com's exchange rate history
OLD_EXCHANGE=re.compile('(?P<month>\d+)/(?P<day>\d+)/(?P<year>\d+),(?P<rate>[\d.]+)')
EXCHANGE=re.compile('"(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+)","(?P<rate>[\d.]+)"')

# A line from OtherAssets.txt
OTHERASSET=re.compile('(?P<name>[\w.-_]+)\s+(?P<type>\w+)\s+(?P<value>[\d.-]+)\s+(?P<date>\d+/\d+/\d+)\s+(?P<change>[\d.]+)\s*\n')

# save.csv
LOCAL_PRICES = os.path.normpath("./data/save.csv")
TEXTSAVE=re.compile('(?P<ticker>[\w^.-]+),(?P<year>[\d]+)-(?P<month>[\d]+)-(?P<day>[\d]+),(?P<price>[\d.]+)')

# PRICE SOURCES
LATEST_PRICES_URL = "http://download.finance.yahoo.com/d/quotes.csv?s=%s&f=sl1d1t1c1ohgv&e=.csv"
HISTORICAL_SHARE_PRICE_URL = "https://finance.google.com/finance/historical?q=%s&startdate=%d-%s-%d&enddate=%d-%s-%d&output=csv"
#HISTORICAL_SHARE_PRICE_URL = "http://ichart.finance.yahoo.com/table.csv?s=%s&a=%d&b=%d&c=%d&d=%d&e=%d&f=%d&g=d&ignore=.csv"
#OLD_HISTORICAL_CURRENCY_PRICE_URL = "http://www.oanda.com/convert/fxhistory?date_fmt=us&date=%d/%d/%d&date1=%d/%d/%d&exch=%s&expr=GBP&lang=en&margin_fixed=0&format=CSV&redirected=1"
HISTORICAL_CURRENCY_PRICE_URL = "http://www.oanda.com/currency/historical-rates/download?quote_currency=%s&end_data=%d-%d-%d&start_date=%d-%d-%d&period=daily&data_range=c&display=absolute&rate=0&price=bid&view=table&base_currency_0=GBP&base_currency_1=&base_currency_2=&base_currency_3=&base_currency_4=&download=csv"

OANDA_MAX_DAYS=28

# MODIFICATIONS
ROK_BANKRUPT=datetime.date(year=2010,month=11,day=8)
CPT_REDENOMINATED=datetime.date(year=2009,month=7,day=28)

ALPHA_HISTORICAL_URL = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=%s&apikey=%s"

ALPHA_CURRENT_URL = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=%s&apikey=%s"

ALPHA_FX_URL = "https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=%s&to_symbol=GBP&apikey=%s"

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
        if ticker.find("IS15") != -1 and price > 12000:
            price = 0
        if ticker.find("BRK-B") != -1:
            dayBefore = priceDate - datetime.timedelta(days = 1)
            price *= prices[("USD", dayBefore)]
            if price > 10000 and priceDate < datetime.date(year=2010,month=2,day=1):
                price /= 50
        if ticker.find("TEG") != -1:
            lastDay = priceDate
            while ("Euro", lastDay) not in prices:
                lastDay = lastDay - datetime.timedelta(days = 1)
            price *= prices[("Euro", lastDay)]
        if "NWBD" in ticker and price > 800:
            price /= 100

        return price

    @staticmethod
    def fixPriceGaps(prices):
        # Iterate through learning tickers and first and last dates
        # Iterate through filling in gaps
        tickers = []
        dates = {}
        for (ticker, date) in sorted(list(prices.keys()), key=operator.itemgetter(1)):
            if not ticker in tickers:
                tickers.append(ticker)
                dates[ticker] = [date, date]
            if date < dates[ticker][0]:
                dates[ticker][0] = date
            elif date > dates[ticker][1]:
                dates[ticker][1] = date

        for (ticker, date) in sorted(list(prices.keys()), key=operator.itemgetter(1)):
            while dates[ticker][0] < date - datetime.timedelta(days = 1) and dates[ticker][0] < dates[ticker][1]:
                dates[ticker][0] += datetime.timedelta(days = 1)
                prices[(ticker, dates[ticker][0])] = prices[(ticker, dates[ticker][0] - datetime.timedelta(days = 1))]
            dates[ticker][0] = date

    @staticmethod
    def fixLastPrices(prices, currentTickers):
        # Iterate through learning tickers and first and last dates
        # Iterate through filling in gaps
        tickers = []
        dates = {}
        for (ticker, date) in sorted(list(prices.keys()), key=operator.itemgetter(1)):
            if not ticker in tickers:
                tickers.append(ticker)
                dates[ticker] = [date, date]
            if date < dates[ticker][0]:
                dates[ticker][0] = date
            elif date > dates[ticker][1]:
                dates[ticker][1] = date

        for ticker in currentTickers:
             while dates[ticker][1] < datetime.date.today():
                 dates[ticker][1] += datetime.timedelta(days = 1)
                 prices[(ticker, dates[ticker][1])] = prices[(ticker, dates[ticker][1] - datetime.timedelta(days = 1))] 

# Methods for building URLs
    @staticmethod
    def currentPricesUrl(tickerList):
        portfolioString=""
        for ticker in tickerList:
            portfolioString="%s%s+"%(portfolioString, ticker)

        url = LATEST_PRICES_URL % portfolioString
        return url
    
    @staticmethod
    def currentPriceUrl(ticker):
        alpha_key = open("./data/alpha_vantage.txt").readline()
        url = ALPHA_CURRENT_URL%(ticker, alpha_key)
        return url 

    @staticmethod
    def alphaKey():
        return open("./data/alpha_vantage.txt").readline()

    @staticmethod
    def historicalPricesUrl(ticker, startDate, lastDate, currency = False):
        urls = []
        if not currency:
            #urls.append(HISTORICAL_SHARE_PRICE_URL%(
            #            ticker,
            #            startDate.month - 1,
            #            startDate.day,
            #            startDate.year,
            #            lastDate.month - 1,
            #            lastDate.day,
            #            lastDate.year))
            urls.append(HISTORICAL_SHARE_PRICE_URL%(
                        ticker,
                        startDate.day,
                        startDate.strftime('%b'),
                        startDate.year,
                        lastDate.day,
                        lastDate.strftime('%b'),
                        lastDate.year))
        else: 
            fixedTicker = "EUR" if ticker == "Euro" else ticker
            urls.append(ALPHA_FX_URL%(fixedTicker, Price.alphaKey()))
            print(urls[-1])

        return urls

    # Methods for loading and parsing info from the web
    @staticmethod
    def loadCurrentPricesFromWeb(tickerList, prices, urlCache):
        for ticker in tickerList:
            if ticker == "NWBD.L":
                continue
            url = Price.currentPriceUrl(ticker)
            print(url)
            try:
                json_string = urlCache.read_url(url)
                json_parsed = json.loads(json_string) 
                price = float(json_parsed['Global Quote']['05. price'])
                price = Price.fixRawPrice(ticker, price, datetime.date.today(), prices)
                prices[(ticker, datetime.date.today())] = price
            except Exception:
                print("Error!")
                traceback.print_exception(*sys.exc_info())


        return prices

    @staticmethod
    def getCurrencyHistory(currency, startDate, endDate, prices, urlCache):
        ticker = currency
        if ticker == "Euro":
            ticker = 'EUR'

        url = Price.historicalPricesUrl(currency, startDate, endDate, True)[-1]

        try: 
            json_string = urlCache.read_url(url)
            json_parsed = json.loads(json_string)
            for day, data in json_parsed['Time Series FX (Daily)'].items():
                 currencyDate = datetime.datetime.strptime(day, "%Y-%m-%d").date()
                 price = float(data['4. close']) * 100
                 prices[(currency, currencyDate)] = price
        except Exception:
            print("Error!")
            traceback.print_exception(*sys.exc_info())

    @staticmethod
    def loadHistoricalPricesFromWeb(ticker, startDate, endDate, prices, urlCache):
        url = Price.historicalPricesUrl(ticker, startDate, endDate, currency = False)[0]
        html = urlCache.read_url(url)

        for line in YAHOODAY.findall(html):
            print(line)
#            priceDate = datetime.datetime.strptime(line[0], "%Y-%m-%d").date()
            priceDate = datetime.datetime.strptime(line[0], "%d-%b-%y").date()
            closePrice = float(line[4])
            closePrice = Price.fixRawPrice(ticker, closePrice, priceDate, prices)
            if closePrice != 0:
                prices[(ticker, priceDate)] = closePrice

    # For each investment, get its price history
    @staticmethod
    def loadHistoricalPricesFromDisk(prices, file = LOCAL_PRICES, inputStream = None):
        if not inputStream:
            inputStream = open(file)
        for line_bytes in inputStream:
            line = line_bytes.decode("utf-8")
            parsedline = TEXTSAVE.match(line)
            if parsedline != None:
                ticker = parsedline.group('ticker')
                price = float(parsedline.group('price'))
                date = datetime.date(int(parsedline.group('year')), \
                                     int(parsedline.group('month')), \
                                     int(parsedline.group('day')))
                if price != 0:
                    prices[(ticker, date)] = price
            else:
                print("Duff line in %s: %s"%(LOCAL_PRICES, line))

    @staticmethod
    def writePrices(file, prices, keys):
        for item in keys:
            file.write("%s,%s,%s\n"%(item[0],item[1].strftime("%Y-%m-%d"),prices[item]))

    @staticmethod
    def savePricesToDisk(prices, outStream = None):
        if outStream:
            Price.writePrices(outStream, prices, prices)
        else:
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

