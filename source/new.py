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

from urlcache import urlcache

def cacheUrls(tickerList):
    urls = []
    urls.append(Price.currentPricesUrl(tickerList))
    
    urlCache = urlcache(urls)
    urlCache.cache_urls()
    return urlCache
    
#
# Main code
#    
    
# Read all transactions from disk    
transactions = transaction.readTransactions()

# Build a list of all mentioned tickers
tickerList = []
for transaction in transactions:
    if transaction.ticker not in tickerList:
        tickerList.append(transaction.ticker)

# Start reading all the HTML we're going to need now.    
urlCache = cacheUrls(tickerList)

# Load current prices from the Web
prices = {}
Price.loadCurrentPricesFromWeb(tickerList, prices, urlCache)

# Build a history of our transactions
history = History(transactions)

# Get today's portfolio
portfolio = history.getPortfolio(datetime.date.today())

portfolio.notePrices(datetime.date.today(), prices)

# And dump a quick summary
portfolio.printSummary()

# List purchases
portfolio.printPurchases()