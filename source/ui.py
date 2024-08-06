#
# Standard UI
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

from screenOutput import screenOutput
from price import Price
from transaction import transaction
from history import History
from investment import investment
from yfPriceLoader import yfPriceLoader

class ui(object):

    TEMP_PORTFOLIO = os.path.normpath("./tempPortfolio.txt")

    outputPortfolio = None

    def __init__(self, history, portfolio, investments):
        self.history = history
        self.portfolio = portfolio
        self.investments = investments
        self.portfolioStream = None
        self.commands = {
            # General
            "interactive"  : (self.interactive),
            "exit"         : (sys.exit),
            "help"         : (self.help),
            "debug"        : (self.debug, "Enter PDB debugger"),
            "reload"       : (self.reload, "Refresh all data"),
            "eval"         : (eval, "Run a python command", "<args>"),

            # Print to screen
            "summary"      : (self.summary, "Current portfolio"),
            "purchases"    : (self.purchases, "Ranked list of purchases"),
            "income"       : (self.income, "All dividends received"),
            "comparedates" : (self.compareDates, "Compare two dates", "<earlier date> <later date>"),
            "compare"      : (self.compareDates, "=compareDates"),
            "capital"      : (self.capitalGain, "Capital gain/loss summary"),
            "tax"          : (self.tax, "Tax details for a given year", "<year>"),
            "print"        : (self.summary, "=summary"),
            "yield"        : (self.portfolioYield, "Current portfolio estimated forward yield"),
            "transactions" : (self.transactions, "List of all transactions"),
            "shareinfo"    : (self.shareInfo, "Info on a particular share", "<ticker> [startDate] [endDate]"),

            # Publish/write
            "publish"      : (self.publish, "Publish to web"),
            "tidy"         : (self.tidy, "Tidy local price database"),
            "dividend"     : (self.dividend, "Record dividend transaction", "<ticker> <Ex-div-date> <Div-date> <Per-share-amount>"),
            "sell"         : (self.sell, "Record sell transaction", "<ticker> <Sale-date> <Number> <Price> <Commission>"),
            "buy"          : (self.buy, "Record buy transaction", "<ticker> <Buy-date> <Number> <Price> <Commission>"),
            "sync"         : (self.sync, "Sync portfolio to web"),
        }

    def interactive(self):
        while True:
            try:
                cmd = input("> ")
                self.runCommand(cmd)
            except Exception:
                print("Error!")
                traceback.print_exception(*sys.exc_info())

    def help(self, arg = None):
        print("All dates use YYYY-MM-DD format")
        if arg:
            print("%s"%arg)
            if not isinstance(self.commands[arg], tuple):
                print("Self-explanatory")
            else:
                print("%s"%self.commands[arg][1])
                if len(self.commands[arg]) > 2:
                    print("%s %s"%(arg, self.commands[arg][2]))
        else:
            print("Available commands:")
            for key, command in self.commands.items():
                if isinstance(command, tuple):
                    print("%-14s%s"%(key, command[1]))
                else:
                    print("%-14s"%(key))

    def compareDates(self, startDateString, endDateString = ""):
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

        screenOutput.portfolioDiff(startDate, endDate, self.history)

    def runCommand(self, command, outputStream = None):
        # Handle redirection of stdout to file
        file = None
        if ">" in command:
            command, file = command.split(">")
            command = command.strip()
            file = file.strip()
            outputStream = open(file, "w")

        if outputStream:
            oldStdout = sys.stdout
            sys.stdout = outputStream

        # Now process command itself
        substrings = command.split()
        if substrings[0].lower() in self.commands:
            fun = self.commands[substrings[0].lower()]
            if isinstance(fun, tuple):
                fun = fun[0]
            fun(*substrings[1:])
        else:
            print("Command unrecognized")

        # And restore stdout, if required
        if outputStream:
            sys.stdout = oldStdout
            if file:
                outputStream.close()
                print("Output to %s:"%file)
                readfile = open(file, "r")
                for line in readfile:
                    print(line, end=' ')
                readfile.close()

    def summary(self):
        screenOutput.portfolioSummary(self.portfolio)

    def purchases(self):
        screenOutput.portfolioPurchases(self.portfolio)

    def income(self):
        screenOutput.income(self.history.transactions)

    def capitalGain(self):
        screenOutput.capitalGain(self.portfolio)

    def publish(self):
        # TODO
        return

    def tax(self, year):
        screenOutput.tax(self.history, self.investments, int(year))

    def portfolioYield(self):
        screenOutput.portfolioYield(self.portfolio, self.investments)

    def tidy(self):
        # Sorts the local price database into a sensible order
        Price.writeSorted(self.history.prices)

    def debug(self):
        pdb.set_trace()

    def reload(self):
        # Create the complete portfolio history
        print("Building portfolio history...")
        self.history, self.investments = self.createHistory()
        print("Done")
        print("")

        # Get today's portfolio
        self.portfolio = self.history.getPortfolio(date.today())

    def createHistory(self,
                    portfolioFile = None, 
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
        currencyList = ["USD", "Euro", "NOK", "SEK"]

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

    def dividend(self, ticker, textExdivDate, textDivDate, textPerShareAmount):
        # Parse dates
        try:
            exdivDate = datetime.strptime(textExdivDate, "%Y-%m-%d").date()
            divDate = datetime.strptime(textDivDate, "%Y-%m-%d").date()
        except:
            print("Unable to parse %s or %s as %Y-%m-%d"%(textExdivDate, textDivDate))
            return

        perShareAmount = float(textPerShareAmount)

        numberHeld = self.portfolio.holdings[ticker].number

        transaction.writeTransaction(ticker, exdivDate, numberHeld, "EXDIV", perShareAmount, 0, outputStream = self.portfolioStream)
        transaction.writeTransaction(ticker, divDate, numberHeld, "DIV", perShareAmount, 0, outputStream = self.portfolioStream)

        self.sync()
        self.reload()

    def sell(self, ticker, textSaleDate, textNumber, textPerShareAmount, textCommission):
        # Parse date
        try:
            saleDate = datetime.strptime(textSaleDate, "%Y-%m-%d").date()
        except:
            print("Unable to parse %s as YYYY-MM-DD"%textSaleDate)
            return

        perShareAmount = float(textPerShareAmount)
        commission = float(textCommission)
        number = float(textNumber)

        transaction.writeTransaction(ticker, saleDate, number, "SELL", perShareAmount, commission, outputStream = self.portfolioStream)

        self.reload()

    def buy(self, ticker, textBuyDate, textNumber, textPerShareAmount, textCommission):
        # Parse date
        try:
            buyDate = datetime.strptime(textBuyDate, "%Y-%m-%d").date()
        except:
            print("Unable to parse %s as %Y-%m-%d"%textBuyDate)
            return

        perShareAmount = float(textPerShareAmount)
        commission = float(textCommission)
        number = float(textNumber)

        transaction.writeTransaction(ticker, buyDate, number, "BUY", perShareAmount, commission, outputStream = self.portfolioStream)

        self.reload()

    def transactions(self):
        screenOutput.transactions(self.history.transactions)

    def shareInfo(self, ticker, startDateString = None, endDateString = None):
        if not startDateString:
            startDate = self.history.transactions[0].date
        else:
            startDate = datetime.strptime(startDateString, "%Y-%m-%d").date()

        if not endDateString:
            endDate = date.today()
        else:
            endDate = datetime.strptime(endDateString, "%Y-%m-%d").date()

        screenOutput.shareInfo(self.history, ticker, startDate, endDate)

    def sync(self):
        dir, file = transaction.dirAndFile()
        newPublish.upload(dir, file)


