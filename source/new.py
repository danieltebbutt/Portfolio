#
# Portfolio Tracker 
#
# Refactored as of late 2014
#
# Copyright 2008 Daniel Tebbutt
#

import datetime

from price import Price
from transaction import transaction
from history import History
from investment import investment

from urlcache import urlcache

# Cache all URLs that we are going to load from later
def cacheUrls(tickerList, currencyList, investments, startDate):
    urls = []
    urls.append(Price.currentPricesUrl(tickerList))
    
    for currency in currencyList:
        urls.extend(Price.historicalPricesUrl(currency, startDate, datetime.date.today(), currency = True))
    
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

# Start reading all the HTML we're going to need now.
urlCache = cacheUrls(tickerList, currencyList, investments, startDate)

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

# !! Now load historical prices from the Web

# Build a history of our transactions
history = History(transactions)

# Get today's portfolio
portfolio = history.getPortfolio(datetime.date.today())

portfolio.notePrices(datetime.date.today(), prices)





# And dump a quick summary
portfolio.printSummary()

# List purchases
portfolio.printPurchases()

