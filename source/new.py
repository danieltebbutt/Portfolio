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
import os
import traceback
import json
from datetime import datetime
from datetime import date
from datetime import timedelta

from .screenOutput import screenOutput
from .price import Price
from .transaction import transaction
from .history import History
from .investment import investment
from .urlcache import urlcache
from .amazonPublisher import amazonPublisher
from .yfPriceLoader import yfPriceLoader


# Hack to workaround Python SSL bug
import ssl
from functools import wraps
def sslwrap(func):
    @wraps(func)
    def bar(*args, **kw):
        kw['ssl_version'] = ssl.PROTOCOL_TLSv1
        return func(*args, **kw)
    return bar
ssl.wrap_socket = sslwrap(ssl.wrap_socket)
# End hack

TEMP_PORTFOLIO = os.path.normpath("./tempPortfolio.txt")

def createHistory(portfolioFile = None, 
                  forceReload = False,
                  portfolio_stream = None,
                  price_stream = None,
                  stock_stream = None,
                  update_data = True,
                  price_out_stream = None):
    # Read all transactions from disk
    transactions = transaction.readTransactions(inputFile = portfolioFile, inputStream = portfolio_stream)
    startDate = transactions[0].date

    # And all investments
    investments = investment.learn_investments(transactions, inputStream = stock_stream)

    # Hard code currency list.  !! Should pick these out of investments really.
    currencyList = ["USD", "Euro", "NOK"]

    # Build a history of our transactions
    history = History(transactions)

    # Load what we've got from disk
    prices = {}
    Price.loadHistoricalPricesFromDisk(prices, inputStream = price_stream)

    if update_data:
        tickerList = history.currentTickers()
        loader = yfPriceLoader(tickerList, currencyList)
        loader.getCurrentPrices(prices)

        # Fill in any gaps
        Price.fixPriceGaps(prices)

        # Now save any new data to disk
        Price.savePricesToDisk(prices, outStream = price_out_stream)

    # Fill in any gaps between the last noted price and today
    Price.fixLastPrices(prices, history.currentTickers())

    # Give the prices to our history
    history.notePrices(prices)

    return (history, investments)

def interactive():
    while True:
        try:
            cmd = input("> ")
            runCommand(cmd)
        except Exception:
            print("Error!")
            traceback.print_exception(*sys.exc_info())

def help(arg = None):
    print("All dates use YYYY-MM-DD format")
    if arg:
        print("%s"%arg)
        if not isinstance(commands[arg], tuple):
            print("Self-explanatory")
        else:
            print("%s"%commands[arg][1])
            if len(commands[arg]) > 2:
                print("%s %s"%(arg, commands[arg][2]))
    else:
        print("Available commands:")
        for key, command in commands.items():
            if isinstance(command, tuple):
                print("%-14s%s"%(key, command[1]))
            else:
                print("%-14s"%(key))

def compareDates(startDateString, endDateString = ""):
    # Parse dates
    try:
        startDate = datetime.strptime(startDateString, "%Y-%m-%d").date()
    except:
        print("Unable to parse %s as YYYY-mm-dd"%startDateString)
        return
    try:
        if endDateString:
            endDate = datetime.strptime(endDateString, "%Y-%m-%d").date()
        else:
            endDate = date.today()
    except:
        print("Unable to parse %s as YYYY-MM-DD"%endDateString)
        return

    # Validate input
    if endDate <= startDate:
        print("End date must be later than start date")
        return
    elif endDate > date.today():
        endDate = date.today()

    screenOutput.portfolioDiff(startDate, endDate, history)

def compareShare(ticker):
    global newHistory
    global newInvestments
    global newPortfolio
    
    # Get price info about the ticker
    newPrices = {}
    Price.loadHistoricalPricesFromDisk(newPrices)
    urlCache, currencyInfo, tickerInfoList = cacheUrls([ticker], [], [], None, history.transactions[0].date, newPrices, forceReload = True)
    Price.loadCurrentPricesFromWeb([ticker], newPrices, urlCache)
    for tickerInfo in tickerInfoList:
        Price.loadHistoricalPricesFromWeb(tickerInfo[0], tickerInfo[1], tickerInfo[2], newPrices, urlCache)
    Price.fixPriceGaps(newPrices)
    #urlCache.clean_urls()

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
    print("Building portfolio history...")
    newHistory, newInvestments = createHistory(TEMP_PORTFOLIO, forceReload = True)
    print("Done")
    print("")
    newPortfolio = newHistory.getPortfolio(date.today())

    # And print some info
    print("Hypothetical / real capital gain:   \N{pound sign}%.2f / \N{pound sign}%.2f"%(newPortfolio.capitalGain() / 100, portfolio.capitalGain() / 100))
    print("Real portfolio dividends received:  \N{pound sign}%.2f"%(portfolio.totalDividends() / 100))
    print("Real portfolio yield:                %.2f%%"%(((portfolio.totalDividends() * 365.0 / (history.endDate() - history.startDate()).days)) * 100 / history.averageValue(history.startDate(), history.endDate())))

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
        print("Command unrecognized")

    # And restore stdout, if required
    if file:
        sys.stdout.close()
        sys.stdout = oldStdout
        print("Output to %s:"%file)
        readfile = open(file, "r")
        for line in readfile:
            print(line, end=' ')
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
    awsPublisher = amazonPublisher(history, portfolio, investments)
    awsPublisher.mainPage()

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
    print("Building portfolio history...")
    history, investments = createHistory()
    print("Done")
    print("")

    # Get today's portfolio
    portfolio = history.getPortfolio(date.today())

def dividend(ticker, textExdivDate, textDivDate, textPerShareAmount):
    # Parse dates
    try:
        exdivDate = datetime.strptime(textExdivDate, "%Y-%m-%d").date()
        divDate = datetime.strptime(textDivDate, "%Y-%m-%d").date()
    except:
        print("Unable to parse %s or %s as %Y-%m-%d"%(textExdivDate, textDivDate))
        return

    perShareAmount = float(textPerShareAmount)

    numberHeld = portfolio.holdings[ticker].number

    transaction.writeTransaction(ticker, exdivDate, numberHeld, "EXDIV", perShareAmount, 0)
    transaction.writeTransaction(ticker, divDate, numberHeld, "DIV", perShareAmount, 0)

    sync()
    reload()

def sell(ticker, textSaleDate, textNumber, textPerShareAmount, textCommission):
    # Parse date
    try:
        saleDate = datetime.strptime(textSaleDate, "%Y-%m-%d").date()
    except:
        print("Unable to parse %s as YYYY-MM-DD"%textSaleDate)
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
        print("Unable to parse %s as %Y-%m-%d"%textBuyDate)
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

def sync():
    dir, file = transaction.dirAndFile()
    newPublish.upload(dir, file)

if __name__ == "__main__":
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
        "eval"         : (eval, "Run a python command", "<args>"),

        # Print to screen
        "summary"      : (summary, "Current portfolio"),
        "purchases"    : (purchases, "Ranked list of purchases"),
        "income"       : (income, "All dividends received"),
        "comparedates" : (compareDates, "Compare two dates", "<earlier date> <later date>"),
        "compare"      : (compareDates, "=compareDates"),
        "compareshare" : (compareShare, "Compare portfolio with share or index", "<ticker>"),
        "capital"      : (capitalGain, "Capital gain/loss summary"),
        "tax"          : (tax, "Tax details for a given year", "<year>"),
        "print"        : (summary, "=summary"),
        "yield"        : (portfolioYield, "Current portfolio estimated forward yield"),
        "transactions" : (transactions, "List of all transactions"),
        "shareinfo"    : (shareInfo, "Info on a particular share", "<ticker> [startDate] [endDate]"),

        # Publish/write
        "publish"      : (publish, "Publish to web"),
        "tidy"         : (tidy, "Tidy local price database"),
        "dividend"     : (dividend, "Record dividend transaction", "<ticker> <Ex-div-date> <Div-date> <Per-share-amount>"),
        "sell"         : (sell, "Record sell transaction", "<ticker> <Sale-date> <Number> <Price> <Commission>"),
        "buy"          : (buy, "Record buy transaction", "<ticker> <Buy-date> <Number> <Price> <Commission>"),
        "sync"         : (sync, "Sync portfolio to web"),

    }

    reload()

    # Parse command line args
    for command in sys.argv[1:]:
        runCommand(command)
