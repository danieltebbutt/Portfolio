#
# Portfolio Tracker 
#
# Refactored as of late 2014
#
# Copyright 2008 Daniel Tebbutt
#

#
# Generic IMPORTS
#
import re
import urllib2
import time
import datetime
import operator
import cPickle as pickle
import sys
import os
import math
import threading
import thread
from urlcache import urlcache
import ftplib
import webbrowser

#
# Portfolio tracker IMPORTS
#
from portfolio import portfolio

def command(arg, porty, verbose):
    if arg == "Verbose":
        verbose = True
    elif arg == "Build":
        porty = portfolio(verbose)
    elif arg == "TextLoad":
        porty = portfolio(verbose, text_mode = True)
    elif arg == "Load":
        savefile = open ( '.\\data\\portfolio.save', 'r')
        porty = pickle.load(savefile)
        savefile.close()
    elif arg.startswith("Eval"):
        crap1, crap2, cmd = arg.partition("Eval ")
        eval(cmd)
    elif arg == "Debug":
        trace.enable()
    elif arg == "Exit":
        exit(0)
    elif arg == "Help" or arg == "?":
        print "Build     = Build portfolio from scratch."
        print "Load      = Load saved portfolio from disk."
        print "Update    = Update previously built or loaded portfolio."
        print "Save      = Save portfolio to disk."
        print "Dump      = Dump .csv file summarizing portfolio performance."
        print "Print     = Print summary of portfolio."
        print "Exit      = Exit interactive mode."
        print "Eval      = Evaluate Python command."
        print "Compare   = Compare two dates."
        print "Breakdown = Portfolio breakdown.  Optional parms: percent,headings,currency"
        print "Publish   = Print an HTML portfolio page"
        print "Match     = Match ex-div to div"
    else:
        if porty == None:
            print "No data loaded or built! Cannot %s"%arg
            exit
        elif arg == "Update":
            porty.update()
        elif arg == "Save":
            savefile = open ( '.\\portfolio.save', 'w')
            pickle.dump(porty, savefile)
            savefile.close()
            print "portfolio saved"
        elif arg == "Dump":
            porty.dump()
            porty.dump_shares()
            print "csv files dumped"
        elif arg == "Diags":
            porty.print_diags()
        elif arg == "Print":
            porty.print_all()
        elif arg == "Net":
            porty.load_net_worth()
            porty.print_net_worth()
        elif arg.startswith("Breakdown"):
            crap1, crap2, parms = arg.partition("Breakdown ")
            eval("porty.print_share_breakdown(datetime.date.today(), %s)"%parms)
        elif arg == "Value":
            porty.update_tracking()
            porty.print_values()
        elif arg == "Yield":
            porty.investments = porty.learn_investments()
            porty.print_yield()
        elif arg.startswith("Share"):
            crap1, crap2, share = arg.partition("Share ")
            porty.print_share_details(share)
        elif arg == "Income":
            porty.print_income()
        elif arg == "Publish":
            porty.publish()
        elif arg == "DebugPublish":
            porty.publish(True)
        elif arg == "Capital":
            porty.print_capital_gains()
        elif arg == "Match":
            porty.match()
        elif arg == "TextSave":
            porty.text_save()
        elif arg.startswith("Compare"):
            crap, str1, str2 = arg.split(" ")
            date1 = porty.str_to_date(str1)
            date2 = porty.str_to_date(str2)
            if (date1 < date2):
                porty.print_difference(porty.history[date1], porty.history[date2], "Date comparison: %s to %s"%(date1, date2))
            else:
                print "The second date must be later than the first"
        elif arg.startswith("Print"):
            crap, str1 = arg.split(" ")
            date1 = porty.str_to_date(str1)
            porty.print_particular_date(date1)
        elif arg.startswith("Tax"):
            crap, year = arg.split(" ")
            porty.print_tax(year)
        elif arg.startswith("Rates"):
            crap, rate = arg.split(" ")
            porty.print_rates(rate)
        else:
            print "Argument not recognized: %s"%arg
            print "Enter Help for assistance"
    return porty,verbose

#
# MAIN SCRIPT
#
#

porty = None
verbose = False
trace_enabled = False
handle_exceptions = False
for arg in sys.argv[1:]:
    if arg == "Interactive":
        print "Interactive Mode"
        while True:
            cmd = raw_input("?: ")
            if handle_exceptions:
                try:
                    porty,verbose = command(cmd, porty, verbose)
                except SystemExit, e:
                    sys.exit(e)
                except:
                    print "Unexpected error:", sys.exc_info()[0]
            else:
                porty,verbose = command(cmd, porty, verbose)

    else:
        porty,verbose = command(arg, porty, verbose)

