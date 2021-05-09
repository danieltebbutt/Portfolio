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
from .ui import ui

# Hack to workaround Python SSL bug
from functools import wraps

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

if __name__ == "__main__":
    #
    # Main code
    #

    reload()

    interface = ui(history, portfolio, investments)

    # Parse command line args
    for command in sys.argv[1:]:
        interface.runCommand(command)
