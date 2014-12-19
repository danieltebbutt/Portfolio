#
# Portfolio Tracker 
#
# Refactored as of late 2014
#
# Copyright 2008 Daniel Tebbutt
#

import sys
from datetime import datetime
from datetime import date
from datetime import timedelta


from screenOutput import screenOutput
from price import Price
from transaction import transaction
from history import History
from investment import investment

from urlcache import urlcache

import newPublish

# Cache all URLs that we are going to load from later
def cacheUrls(tickerList, currencyList, investments, history, startDate, prices):
    urls = []
    urls.append(Price.currentPricesUrl(history.currentTickers()))
    
    lastDates = Price.lastDates(prices, currencyList + tickerList)
    for ticker in currencyList + tickerList:
        if ticker not in lastDates:
            lastDates[ticker] = startDate
    
    currencyInfo = []
    tickerInfo = []
    
    for currency in currencyList:
        if date.today() > lastDates[currency]:
            url = Price.historicalPricesUrl(currency, 
                                            lastDates[currency], 
                                            date.today(), 
                                            currency = True)
            urls.extend(url)
            currencyInfo.append((currency, lastDates[currency], url))
    
    for ticker in tickerList:
        if history.lastHeld(ticker) - timedelta(days = 1) > lastDates[ticker]:
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
    Price.loadCurrentPricesFromWeb(history.currentTickers(), prices, urlCache)

    # Now load historical prices from the Web
    for ticker in tickerInfo:
        Price.loadHistoricalPricesFromWeb(ticker[0], ticker[1], ticker[2], prices, urlCache)

    # Fill in any gaps
    Price.fixPriceGaps(prices)    

    # Give the prices to our history
    history.notePrices(prices)

    # Done with all the HTML that we read
    urlCache.clean_urls()

    # Now save any new data to disk
    Price.savePricesToDisk(prices)
    
    return (history, investments)
    
def interactive():
    while True:
        cmd = raw_input("> ")
        runCommand(cmd)
       
def help():
    for command in commands:
        print command

def compare(startDateString, endDateString = ""):
    # Parse dates
    try:
        startDate = datetime.strptime(startDateString, "%Y-%m-%d").date()
    except:
        print "Unable to parse %s as %Y-%m-%d"%startDateString
        return
    try:
        if endDateString:
            endDate = datetime.strptime(endDateString, "%Y-%m-%d").date()
        else:
            endDate = date.today()
    except:
        print "Unable to parse %s as %Y-%m-%d"%endDateString
        return

    # Validate input
    if endDate <= startDate:
        print "End date must be later than start date"
        return
    elif endDate > date.today():
        endDate = date.today()
    
    screenOutput.portfolioDiff(startDate, endDate, history)
        
def runCommand(command):
    # Handle redirection of stdout to file
    file = None
    if ">" in command:
        command, file = command.split(">")
        command = command.strip()
        file = file.strip()
        oldStdout = sys.stdout
        sys.stdout = open(file, "w")
        
    # Now process command itself
    substrings = command.split()
    if substrings[0].lower() in commands:
        commands[substrings[0].lower()](*substrings[1:])
    else:
        print "Command unrecognized"
        
    # And restore stdout, if required
    if file:
        sys.stdout.close()
        sys.stdout = oldStdout
        print "Output to %s:"%file
        readfile = open(file, "r")
        for line in readfile:
            print line,
        readfile.close()
        
def summary():
    screenOutput.portfolioSummary(portfolio)
    screenOutput.portfolioPurchases(portfolio)

def income():
    screenOutput.income(history.transactions)
        
def capitalGain():
    screenOutput.capitalGain(portfolio)        
        
def publish():
    newPublish.mainPage(history, portfolio, investments)
     
def tax(year):
    screenOutput.tax(history, investments, int(year))
     
def portfolioYield():
    screenOutput.portfolioYield(portfolio, investments)
     
#
# Main code
#    
commands = {
    "interactive" : interactive,
    "exit"        : sys.exit,        
    "help"        : help,
    "summary"     : summary,
    "income"      : income,
    "compare"     : compare,
    "capital"     : capitalGain,
    "publish"     : publish,
    "tax"         : tax,
    "print"       : summary,
    "yield"       : portfolioYield,
    
}

# TODO:
# Portfolio yield

# Create the complete portfolio history
print "Building portfolio history..."
history, investments = createHistory()
print "Done"
print ""

# Get today's portfolio
portfolio = history.getPortfolio(date.today())

# Parse command line args
for command in sys.argv[1:]:
    runCommand(command)
    