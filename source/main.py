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

from screenOutput import screenOutput
from price import Price
from transaction import transaction
from history import History
from investment import investment
from yfPriceLoader import yfPriceLoader
from ui import ui

# Hack to workaround Python SSL bug
from functools import wraps

if __name__ == "__main__":
    #
    # Main code
    #

    interface = ui(None, None, None)
    interface.reload()

    # Parse command line args
    for command in sys.argv[1:]:
        interface.runCommand(command)
