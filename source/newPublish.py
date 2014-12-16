# Web publishing

import os
import webbrowser
from os import listdir
from os.path import isfile, join
from datetime import timedelta
from datetime import datetime

TEMPLATE_DIR = ".\\templates"
OUTPUT_DIR = ".\\output"
DESTINATION = "danieltebbutt.com"

chartIndex = 1

def upload(filename):
    outputfile = open("%s\\%s"%(OUTPUT_DIR, filename), 'rb')

    session = ftplib.FTP("ftp.%s"%DESTINATION)
    password = getpass.getpass("Password?")
    session.login(DESTINATION, password)
    session.storbinary("STOR wwwroot\\%s"%filename, outputfile)
    outputfile.close()
    session.quit()
    
def display():
    webbrowser.open("http://www.%s/%s"%(DESTINATION, FILENAME))

def writeScriptHeader(outputfile):
    outputfile.write("\
<script type=\"text/javascript\" src=\"https://www.google.com/jsapi\"></script>\n\
<script type=\"text/javascript\">\n\
google.load(\"visualization\", \"1\", {packages:[\"corechart\"]});\n\
google.setOnLoadCallback(drawChart);\n\
function drawChart() {\n")

def writeScriptFooter(outputfile):
    outputfile.write("\
}\n\
</script>\n")

def writeCurrent(outputfile, history, portfolio, investments):
    outputfile.write("<DIV ALIGN=\"Left\"><B>Current portfolio (%d%% of peak size)</B><BR></DIV>\n"%(portfolio.value() * 100 / history.peakValue()))

    outputfile.write(
"<TABLE WIDTH=100%% BORDER=1 BORDERCOLOR=\"#888888\" CELLPADDING=2 CELLSPACING=0 CLASS=\"sortable\" style=\"font-size:12px\">\n\
  <TR VALIGN=TOP>\
<TH>Share</TH>\
<TH>Ticker</TH>\
<TH TITLE=\"Percentage of portfolio value\">Percentage</TH>\
<TH TITLE=\"Average purchase price\">Bought at (p)</TH>\
<TH TITLE=\"Current price\">Current (p)</TH>\
<TH TITLE=\"Average per-share accumulated dividends received\">Dividends (p)</TH>\
<TH TITLE=\"Average per-share profit, including capital gain and dividends received\">Profit</TH>\
<TH TITLE=\"Average annual per-share profit, including capital gain and dividends received\">Annual profit</TH>\
</TR>\n")

    for ticker in portfolio.currentTickers():
        holding = portfolio.holdings[ticker]
        outputfile.write("  <TR VALIGN=TOP>")
        
        # Full name
        outputfile.write("<TD>%s</TD>"%investments[ticker].fullname)
        
        # Ticker
        outputfile.write("<TD>%s</TD>"%ticker)
        
        # Percentage of total value
        outputfile.write("<TD>%.1f%%"%(100 * holding.value() / portfolio.value()))
        
        # Average purchase price
        outputfile.write("<TD>%.1f</TD>"%holding.averagePurchasePrice())
        
        # Current price
        outputfile.write("<TD>%.1f</TD>"%holding.price)
        
        # Dividends
        outputfile.write("<TD>%.1f</TD>"%holding.perShareDividends(active = True))
        
        # Profit
        profit = 100 * holding.activeProfit() / holding.activeCost()
        outputfile.write("<TD><FONT COLOR=\"%s\">%.1f%%</FONT></TD>"%(
                         ("#008000" if profit >= 0 else "#800000"), 
                         profit))
        
        # Annual profit
        profit = 100 * ((1 + (holding.activeProfit() / holding.activeCost())) ** (365.0 / holding.averageHoldingPeriod()) - 1)
        outputfile.write("<TD><FONT COLOR=\"%s\">%.1f%%</FONT></TD>"%(
                         ("#008000" if profit >= 0 else "#800000"), 
                         profit))
                         
        outputfile.write("\n")

    outputfile.write("</TABLE>\n")
    
def writePrevious(outputfile, history, portfolio, investments):
    outputfile.write("")
    
def writeProfit(outputfile, history, portfolio, investments):
    outputfile.write("")
    
def writeSize(outputfile, history, portfolio, investments):
    outputfile.write("")
    
def writeNet(outputfile, history, portfolio, investments):
    outputfile.write("")
    
def writeSector(outputfile, history, portfolio, investments):
    outputfile.write("")
    
def writeClass(outputfile, history, portfolio, investments):
    outputfile.write("Test 7<BR>\n")
            
def writeDate(outputfile, history, portfolio, investments):
    outputfile.write("%s"%datetime.today().date())            
            
def actionTemplate(history, portfolio, investments, template):

    # tag: (function, isScript)
    tags = {"###CURRENT###"      : (writeCurrent, False),
            "###PREVIOUS###"     : (writePrevious, False),
            "###PROFIT###"       : (writeProfit, True),
            "###SIZE###"         : (writeSize, True),
            "###NET###"          : (writeNet, True),
            "###SECTOR###"       : (writeSector, True),
            "###CLASS###"        : (writeClass, True),
            "###DATE###"         : (writeDate, False),
            }

    fileStream = open(join(TEMPLATE_DIR,template), 'r')
    outputfile = open(join(OUTPUT_DIR,template), 'w')

    writeTags = {}
    chartIndex = 1

    for line in fileStream:
        if line.strip() in tags and tags[line.strip()][1]:
            writeTags[line.strip()] = 0

    fileStream.seek(0)

    for line in fileStream:
        if "</head>" in line.lower():
            if len(writeTags) > 0:
                writeScriptHeader(outputfile)
                for tag in writeTags:
                    writeTags[tag] = chartIndex
                    tags[tag][0](outputfile, history, portfolio, investments)
                writeScriptFooter(outputfile)
            outputfile.write(line)
        elif line.strip() in writeTags:
            outputfile.write("<div id=\"chart_div%d\"></div>\n"%writeTags[tag])
        elif line.strip() in tags:
            tags[line.strip()][0](outputfile, history, portfolio, investments)
        else:
            outputfile.write(line)
    outputfile.close()    
    
def mainPage(history, portfolio, investments):

    templateFiles = [ f for f in listdir(TEMPLATE_DIR) if isfile(join(TEMPLATE_DIR, f)) ]

    for template in templateFiles:
        actionTemplate(history, portfolio, investments, template)
    
    #upload()
    
    #display()
    