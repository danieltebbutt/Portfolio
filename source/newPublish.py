# Web publishing

import os
import webbrowser
import ftplib
import getpass
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
    
def display(filename):
    webbrowser.open("http://www.%s/%s"%(DESTINATION, filename))

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

    

    for ticker in sorted(portfolio.currentTickers(), key=lambda x: portfolio.holdings[x].value(), reverse = True):
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
    outputfile.write("<B>Former holdings</B><BR>\n")
    outputfile.write(
"<TABLE WIDTH=100%% BORDER=1 BORDERCOLOR=\"#888888\" CELLPADDING=2 CELLSPACING=0 CLASS=\"sortable\" style=\"font-size:12px\">\n\
<TR VALIGN=TOP>\n\
<TH>Share</TH>\n\
<TH>Ticker</TH>\n\
<TH TITLE=\"Average purchase price\">Bought at (p)</TH>\n\
<TH TITLE=\"Average sale price\">Sold at (p)</TH>\n\
<TH TITLE=\"Average per-share accumulated dividends received\">Dividends (p)</TH>\n\
<TH TITLE=\"Average per-share profit, including capital gain and dividends received\">Profit</TH>\n\
<TH TITLE=\"Average annual per-share profit, including capital gain and dividends received\">Annual profit</TH>\n\
</TR>\n")

    purchases = []
    for ticker, holding in portfolio.holdings.iteritems():
        purchases.extend(holding.inactivePurchases())
        
    purchases.sort(key=lambda x: x.percent_profit(), reverse = True)

    for purchase in purchases:
        outputfile.write("  <TR VALIGN=TOP>")
        
        # Full name
        outputfile.write("<TD>%s</TD>"%investments[purchase.ticker].fullname)
        
        # Ticker
        outputfile.write("<TD>%s</TD>"%purchase.ticker)
        
        # Average purchase price
        outputfile.write("<TD>%.1f</TD>"%purchase.purchase_price)
        
        # Sale price
        outputfile.write("<TD>%.1f</TD>"%purchase.sale_price)
        
        # Dividends
        outputfile.write("<TD>%.1f</TD>"%purchase.dividends_received)
        
        # Profit
        profit = purchase.percent_profit()
        outputfile.write("<TD><FONT COLOR=\"%s\">%.1f%%</FONT></TD>"%(
                         ("#008000" if profit >= 0 else "#800000"), 
                         profit))
        
        # Annual profit
        profit = 100 * ((1 + (purchase.percent_profit() / 100)) ** (365.0 / purchase.holdingPeriod()) - 1)
        outputfile.write("<TD><FONT COLOR=\"%s\">%.1f%%</FONT></TD>"%(
                         ("#008000" if profit >= 0 else "#800000"), 
                         profit))
                         
        outputfile.write("\n")

    outputfile.write("</TABLE>\n")
    
def writeProfit(outputfile, history, portfolio, investments):
    global chartIndex

    outputfile.write("\
var data%d = google.visualization.arrayToDataTable([\n\
['Month', 'Profit'],\n"%chartIndex)
    
    totalDays = history.endDate() - history.startDate()
    
    peakInvested = history.peakInvested()
    for days in range(0, totalDays.days, 28):
        date = history.startDate() + timedelta(days = days)
        outputfile.write("[new Date(%d,%d,%d),%.1f],\n"%(
                         date.year,
                         date.month - 1,
                         date.day,
                         100 * history.getPortfolio(date).totalProfit() / peakInvested
                         ))
    
    outputfile.write("]);\n\
\n\
  var options%d = {\n\
    title: 'Profit',\n\
    legend: {position: 'none'},\n\
  };\n\
\n\
  var chart%d = new google.visualization.LineChart(document.getElementById('chart_div%d'));\n\
\n\
  chart%d.draw(data%d, options%d);\n"%(chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex))
    chartIndex += 1
    
def writeSize(outputfile, history, portfolio, investments):
    global chartIndex

    outputfile.write("\
var data%d = google.visualization.arrayToDataTable([\n\
['Month', 'Size'],\n"%chartIndex)
    
    totalDays = history.endDate() - history.startDate()
    
    peakValue = history.peakValue()
    for days in range(0, totalDays.days, 28):
        date = history.startDate() + timedelta(days = days)
        outputfile.write("[new Date(%d,%d,%d),%.1f],\n"%(
                         date.year,
                         date.month - 1,
                         date.day,
                         100 * history.getPortfolio(date).totalValue() / peakValue
                         ))
    
    outputfile.write("]);\n\
\n\
  var options%d = {\n\
    title: 'Size',\n\
    legend: {position: 'none'},\n\
  };\n\
\n\
  var chart%d = new google.visualization.LineChart(document.getElementById('chart_div%d'));\n\
\n\
  chart%d.draw(data%d, options%d);\n"%(chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex))
    chartIndex += 1
    
def writeNet(outputfile, history, portfolio, investments):
    global chartIndex

    outputfile.write("\
var data%d = google.visualization.arrayToDataTable([\n\
['Month', 'Size', 'Net invested'],\n"%chartIndex)
    
    totalDays = history.endDate() - history.startDate()
    
    peakValue = history.peakValue()
    for days in range(0, totalDays.days, 28):
        date = history.startDate() + timedelta(days = days)
        outputfile.write("[new Date(%d,%d,%d),%.1f,%.1f],\n"%(
                         date.year,
                         date.month - 1,
                         date.day,
                         100 * history.getPortfolio(date).totalValue() / peakValue,
                         100 * history.getPortfolio(date).netInvested() / peakValue
                         ))
    
    outputfile.write("]);\n\
\n\
  var options%d = {\n\
    title: 'Size vs Net Invested',\n\
    legend: {position: 'none'},\n\
  };\n\
\n\
  var chart%d = new google.visualization.LineChart(document.getElementById('chart_div%d'));\n\
\n\
  chart%d.draw(data%d, options%d);\n"%(chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex))
    chartIndex += 1
    
def writeSector(outputfile, history, portfolio, investments):
    pass
    
def writeClass(outputfile, history, portfolio, investments):
    pass
    
def writeDate(outputfile, history, portfolio, investments):
    outputfile.write("%s"%datetime.today().date())            
            
def actionTemplate(history, portfolio, investments, template):
    global chartIndex
    
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
            outputfile.write("<div id=\"chart_div%d\" style=\"width: 600px; height: 400px;\"></div>\n"%writeTags[line.strip()])
        elif line.strip() in tags:
            tags[line.strip()][0](outputfile, history, portfolio, investments)
        else:
            outputfile.write(line)
    outputfile.close()    
    
def mainPage(history, portfolio, investments):

    templateFiles = [ f for f in listdir(TEMPLATE_DIR) if isfile(join(TEMPLATE_DIR, f)) ]

    for template in templateFiles:
        actionTemplate(history, portfolio, investments, template)
        upload(template)    
        display(template)
    
    