#
# Portfolio Tracker 
#
# Refactored as of late 2014
#
# Copyright 2008 Daniel Tebbutt
#

import datetime

from transaction import transaction
from history import History

transactions = transaction.readTransactions()
history = History(transactions)

portfolio = history.getPortfolio(datetime.date.today())
        
portfolio.printSummary()        