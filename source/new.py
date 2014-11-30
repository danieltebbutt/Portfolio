#
# Portfolio Tracker 
#
# Refactored as of late 2014
#
# Copyright 2008 Daniel Tebbutt
#

import datetime
from screenOutput import screenOutput

from price import Price
from transaction import transaction
from history import History
from investment import investment

from urlcache import urlcache

# Cache all URLs that we are going to load from later
def cacheUrls(tickerList, currencyList, investments, history, startDate):
    urls = []
    urls.append(Price.currentPricesUrl(tickerList))
    
    for currency in currencyList:
        urls.extend(Price.historicalPricesUrl(currency, startDate, datetime.date.today(), currency = True))
    
    for ticker in tickerList:
        urls.extend(Price.historicalPricesUrl(ticker, history.firstHeld(ticker), history.lastHeld(ticker), currency = False))
    
    urlCache = urlcache(urls)
    urlCache.cache_urls()
    return urlCache
    
#
# Main code
#    
    
# Read all transactions from disk    
transactions = transaction.readTransactions()
startDate = transactions[0].date

# And all investments
investments = investment.learn_investments(transactions)

# Build a list of all mentioned tickers
tickerList = []
for transaction in transactions:
    if transaction.ticker not in tickerList:
        tickerList.append(transaction.ticker)

# Hard code currency list.  !! Should pick these out of investments really.        
currencyList = ["USD", "Euro", "NOK"]        

# Build a history of our transactions
history = History(transactions)

# Start reading all the HTML we're going to need now.
urlCache = cacheUrls(tickerList, currencyList, investments, history, startDate)

# Load currency histories
prices = {}
for currency in currencyList:
    Price.getCurrencyHistory(currency, 
                             startDate, 
                             prices, 
                             urlCache,                             
                             Price.historicalPricesUrl(currency, startDate, datetime.date.today(), currency = True))

# Load current prices from the Web
Price.loadCurrentPricesFromWeb(tickerList, prices, urlCache)

# Now load historical prices from the Web
for ticker in tickerList:
    Price.loadHistoricalPricesFromWeb(ticker, history.firstHeld(ticker), history.lastHeld(ticker), prices, urlCache)

Price.fixPriceGaps(prices)    

history.notePrices(prices)
    
# Get today's portfolio
portfolio = history.getPortfolio(datetime.date.today())

# And dump a quick summary
portfolio.printSummary()

# List purchases
portfolio.printPurchases()

# Get a previous day's portfolio
portfolio_start_2014 = history.getPortfolio(datetime.date(year = 2014, month = 1, day = 1))

portfolio_start_2014.printSummary()

screenOutput.printIncome(transactions)


