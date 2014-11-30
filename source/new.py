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
def cacheUrls(tickerList, currencyList, investments, history, startDate, prices):
    urls = []
    urls.append(Price.currentPricesUrl(tickerList))
    
    lastDates = Price.lastDates(prices, currencyList + tickerList)
    for ticker in lastDates:
        print ticker, lastDates[ticker]
    
    for ticker in currencyList + tickerList:
        if ticker not in lastDates:
            lastDates[ticker] = startDate
    
    currencyInfo = []
    tickerInfo = []
    
    for currency in currencyList:
        if datetime.date.today() > lastDates[currency]:
            url = Price.historicalPricesUrl(currency, 
                                            lastDates[currency], 
                                            datetime.date.today(), 
                                            currency = True)
            urls.extend(url)
            currencyInfo.append((currency, lastDates[currency], url))
    
    for ticker in tickerList:
        if history.lastHeld(ticker) - datetime.timedelta(days = 1) > lastDates[ticker]:
            url = Price.historicalPricesUrl(ticker, 
                                            max(lastDates[ticker], history.firstHeld(ticker)), 
                                            history.lastHeld(ticker), 
                                            currency = False)
            urls.extend(url)
            tickerInfo.append((ticker, max(lastDates[ticker], history.firstHeld(ticker)), history.lastHeld(ticker), url))
     
    urlCache = urlcache(urls)
    urlCache.cache_urls()
    return urlCache, currencyInfo, tickerInfo

def createHistory():
    # Read all transactions from disk    
    transactions = transaction.readTransactions()
    startDate = transactions[0].date

    # And all investments
    investments = investment.learn_investments(transactions)

    # Build a list of all mentioned tickers
    tickerList = []
    for trans in transactions:
        if trans.ticker not in tickerList:
            tickerList.append(trans.ticker)

    # Hard code currency list.  !! Should pick these out of investments really.        
    currencyList = ["USD", "Euro", "NOK"]        

    # Build a history of our transactions
    history = History(transactions)

    # Load what we've got from disk
    prices = {}
    Price.loadHistoricalPricesFromDisk(prices)

    # Start reading all the HTML we're going to need now.
    urlCache, currencyInfo, tickerInfo = cacheUrls(tickerList, currencyList, investments, history, startDate, prices)

    # Load currency histories
    for currency in currencyInfo:
        Price.getCurrencyHistory(currency[0], 
                                 currency[1], 
                                 prices, 
                                 urlCache,                             
                                 currency[2])

    # Load current prices from the Web
    Price.loadCurrentPricesFromWeb(tickerList, prices, urlCache)

    # Now load historical prices from the Web
    for ticker in tickerInfo:
        Price.loadHistoricalPricesFromWeb(ticker[0], ticker[1], ticker[2], prices, urlCache)

    Price.fixPriceGaps(prices)    

    history.notePrices(prices)

    return history
    
    
#
# Main code
#    
history = createHistory()

# Get today's portfolio
portfolio = history.getPortfolio(datetime.date.today())

# And dump a quick summary
portfolio.printSummary()

# List purchases
portfolio.printPurchases()

# Get a previous day's portfolio
portfolio_start_2014 = history.getPortfolio(datetime.date(year = 2014, month = 1, day = 1))

portfolio_start_2014.printSummary()

screenOutput.printIncome(history.transactions)


