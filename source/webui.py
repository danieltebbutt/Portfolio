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

from ui import ui

class webui(ui):

    def __init__(self, history, portfolio, investments, portfolioStream):
        super(webui, self).__init__(history, portfolio, investments)
        self.portfolioStream = portfolioStream
        for command in [ "eval", "interactive", "exit", "debug", "reload", "publish", "tidy", "sync" ]:
            del self.commands[command]

    def reload(self):
        pass

    def sync(self):
        pass


