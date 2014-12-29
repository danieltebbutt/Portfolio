#
# Portfolio Tracker 
#
# Refactored late 2014
#
# Copyright 2008 Daniel Tebbutt
#

import pdb
import sys
import copy
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

TEMP_PORTFOLIO = ".\\tempPortfolio.txt"

# Cache all URLs that we are going to load from later
def cacheUrls(tickerList, currencyList, investments, history, startDate, prices):
    urls = []
    if history:
        urls.append(Price.currentPricesUrl(history.currentTickers()))
    else:
        urls.append(Price.currentPricesUrl(tickerList))
    
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
        if history:
            lastHeld = history.lastHeld(ticker)
            firstHeld = history.firstHeld(ticker)
        else:
            lastHeld = date.today()
            firstHeld = startDate
        if lastHeld - timedelta(days = 1) > lastDates[ticker]:
            url = Price.historicalPricesUrl(ticker, 
                                            max(lastDates[ticker], firstHeld), 
                                            lastHeld, 
                                            currency = False)
            urls.extend(url)
            tickerInfo.append((ticker, max(lastDates[ticker], firstHeld), lastHeld, url))
     
    urlCache = urlcache(urls)
    urlCache.cache_urls()
    return urlCache, currencyInfo, tickerInfo

def createHistory(portfolioFile = None):
    # Read all transactions from disk    
    transactions = transaction.readTransactions(portfolioFile)
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
       
def help(arg = None):
    print "All dates use YYYY-MM-DD format"
    if arg:
        print "%s"%arg
        if not isinstance(commands[arg], tuple):
            print "Self-explanatory"
        else:
            print "%s"%commands[arg][1]
            if len(commands[arg]) > 2:
                print "%s %s"%(arg, commands[arg][2])
    else:
        print "Available commands:"
        for key, command in commands.iteritems():
            if isinstance(command, tuple):            
                print "%-14s%s"%(key, command[1])
            else:
                print "%-14s"%(key)

def compareDates(startDateString, endDateString = ""):
    # Parse dates
    try:
        startDate = datetime.strptime(startDateString, "%Y-%m-%d").date()
    except:
        print "Unable to parse %s as YYYY-mm-dd"%startDateString
        return
    try:
        if endDateString:
            endDate = datetime.strptime(endDateString, "%Y-%m-%d").date()
        else:
            endDate = date.today()
    except:
        print "Unable to parse %s as YYYY-MM-DD"%endDateString
        return

    # Validate input
    if endDate <= startDate:
        print "End date must be later than start date"
        return
    elif endDate > date.today():
        endDate = date.today()
    
    screenOutput.portfolioDiff(startDate, endDate, history)
        
def compareShare(ticker):
    # Get price info about the ticker
    newPrices = {}
    Price.loadHistoricalPricesFromDisk(newPrices)
    urlCache, currencyInfo, tickerInfoList = cacheUrls([ticker], [], [], None, history.transactions[0].date, newPrices)
    Price.loadCurrentPricesFromWeb([ticker], newPrices, urlCache)
    for tickerInfo in tickerInfoList:
        Price.loadHistoricalPricesFromWeb(tickerInfo[0], tickerInfo[1], tickerInfo[2], newPrices, urlCache)
    Price.fixPriceGaps(newPrices)    
    urlCache.clean_urls()

    # Generate a new portfolio file with all tickers replaced with this one.
    newTransactions = []
    for tran in history.transactions:
        if tran.action == "BUY" or tran.action == "SELL":
            newTran = copy.copy(tran)
            newTran.ticker = ticker
            value = newTran.number * newTran.price
            newTran.price = newPrices[(ticker, tran.date)]
            newTran.number = value / newTran.price
            newTransactions.append(newTran)
    transaction.writeTransactions(newTransactions, TEMP_PORTFOLIO)          
    
    # Now build an alternate history based on these new transactions
    print "Building portfolio history..."
    newHistory, newInvestments = createHistory(TEMP_PORTFOLIO)
    print "Done"
    print ""
    newPortfolio = newHistory.getPortfolio(date.today())    

    # And print some info
    print "New / old capital gain: %.2f / %.2f"%(newPortfolio.capitalGain() / 100, portfolio.capitalGain() / 100)
    print "old dividends: %.2f"%(portfolio.totalDividends() / 100)
    #screenOutput.portfolioPurchases(newPortfolio)
    #screenOutput.portfolioSummary(newPortfolio)
    #screenOutput.shareInfo(newHistory, "^FTSE", newTransactions[0].date, date.today())
    #print "Existing portfolio average yield: %.2f%%"%((((1 + (portfolio.totalDividends() / history.basisForReturn(history.startDate(), history.endDate()))) ** (365.00 / (history.endDate() - history.startDate()).days)) - 1) * 100)
    
       
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
        fun = commands[substrings[0].lower()]
        if isinstance(fun, tuple):
            fun = fun[0]
        fun(*substrings[1:])
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

def purchases():
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
     
def tidy():
    # Sorts the local price database into a sensible order
    Price.writeSorted(history.prices)
     
def debug():
    pdb.set_trace()
    
def reload():
    global history
    global portfolio
    global investments
    
    # Create the complete portfolio history
    print "Building portfolio history..."
    history, investments = createHistory()
    print "Done"
    print ""

    # Get today's portfolio
    portfolio = history.getPortfolio(date.today())
    
def dividend(ticker, textExdivDate, textDivDate, textPerShareAmount):
    # Parse dates
    try:
        exdivDate = datetime.strptime(textExdivDate, "%Y-%m-%d").date()
        divDate = datetime.strptime(textDivDate, "%Y-%m-%d").date()
    except:
        print "Unable to parse %s or %s as %Y-%m-%d"%(textExdivDate, textDivDate)
        return

    perShareAmount = float(textPerShareAmount)

    numberHeld = portfolio.holdings[ticker].number

    transaction.writeTransaction(ticker, exdivDate, numberHeld, "EXDIV", perShareAmount, 0)
    transaction.writeTransaction(ticker, divDate, numberHeld, "DIV", perShareAmount, 0)
    
    reload()
    
def sell(ticker, textSaleDate, textNumber, textPerShareAmount, textCommission):
    # Parse date
    try:
        saleDate = datetime.strptime(textSaleDate, "%Y-%m-%d").date()
    except:
        print "Unable to parse %s as YYYY-MM-DD"%textSaleDate
        return

    perShareAmount = float(textPerShareAmount)
    commission = float(textCommission)
    number = float(textNumber)

    transaction.writeTransaction(ticker, saleDate, number, "SELL", perShareAmount, commission)
    
    reload()
    
def buy(ticker, textBuyDate, textNumber, textPerShareAmount, textCommission):
    # Parse date
    try:
        buyDate = datetime.strptime(textBuyDate, "%Y-%m-%d").date()
    except:
        print "Unable to parse %s as %Y-%m-%d"%textBuyDate
        return

    perShareAmount = float(textPerShareAmount)
    commission = float(textCommission)
    number = float(textNumber)

    transaction.writeTransaction(ticker, buyDate, number, "BUY", perShareAmount, commission)
    
    reload()
    
def transactions():
    screenOutput.transactions(history.transactions)
    
def shareInfo(ticker, startDateString = None, endDateString = None):
    if not startDateString:
        startDate = history.transactions[0].date
    else:
        startDate = datetime.strptime(startDateString, "%Y-%m-%d").date() 

    if not endDateString:
        endDate = date.today()
    else:
        endDate = datetime.strptime(endDateString, "%Y-%m-%d").date()
        
    screenOutput.shareInfo(history, ticker, startDate, endDate)
    
#
# Main code
#    
commands = {
    # General
    "interactive"  : (interactive),
    "exit"         : (sys.exit),  
    "help"         : (help),
    "debug"        : (debug, "Enter PDB debugger"),
    "reload"       : (reload, "Refresh all data"),
    
    # Print to screen
    "summary"      : (summary, "Current portfolio"),
    "purchases"    : (purchases, "Ranked list of purchases"),
    "income"       : (income, "All dividends received"),
    "comparedates" : (compareDates, "Compare two dates", "<earlier date> <later date>"),
    "compareshare" : (compareShare, "Compare portfolio with share or index", "<ticker>"),
    "capital"      : (capitalGain, "Capital gain/loss summary"),
    "tax"          : (tax, "Tax details for a given year", "<year>"),
    "print"        : (summary, "Current portfolio"),
    "yield"        : (portfolioYield, "Current portfolio estimated forward yield"),
    "transactions" : (transactions, "List of all transactions"),
    "shareinfo"    : (shareInfo, "Info on a particular share", "<ticker> [startDate] [endDate]"),
    
    # Publish/write
    "publish"      : (publish, "Publish to web"),
    "tidy"         : (tidy, "Tidy local price database"),
    "dividend"     : (dividend, "Record dividend transaction", "<ticker> <Ex-div-date> <Div-date> <Per-share-amount>"),
    "sell"         : (sell, "Record sell transaction", "<ticker> <Sale-date> <Number> <Price> <Commission>"),
    "buy"          : (buy, "Record buy transaction", "<ticker> <Buy-date> <Number> <Price> <Commission>"),
    
}

reload()

# Parse command line args
for command in sys.argv[1:]:
    runCommand(command)
    