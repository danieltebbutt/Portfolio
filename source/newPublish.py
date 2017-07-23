# Web publishing

import os
import webbrowser
import ftplib
import getpass
from os import listdir
from os.path import isfile, join
from datetime import timedelta
from datetime import datetime
import ConfigParser
import boto
from boto.s3.key import Key
import posixpath
from htmlOutput import htmlOutput

TEMPLATE_DIR = os.path.normpath("./templates")
OUTPUT_DIR = os.path.normpath("./output")
DESTINATION = "danieltebbutt.com"
DETAIL_DIR = "portfolio"

MOUSEABLE = " onmouseover=\"this.style.background='lightgray'\" onmouseout=\"this.style.background='';\""

chartIndex = 1

def upload(dir, file):

    config = ConfigParser.ConfigParser()
    config.readfp(open('portfolio.ini'))
    type = config.get("newPublish", "type")
    destination = config.get("newPublish", "destination")

    if type == "FTP":
        print "!! Needs work"
    elif type == "AWS":
        s3 = boto.connect_s3()
        bucket = s3.get_bucket(destination)

        k = Key(bucket)
        print "Uploading:"

        pathAndFile = join(dir, file)
        fileStream = open(pathAndFile, 'rb')
        k.key = file
        print file
        k.set_contents_from_file(fileStream)
        fileStream.close()


def uploadAll(local_dir = OUTPUT_DIR):

    config = ConfigParser.ConfigParser()
    config.readfp(open('portfolio.ini'))
    type = config.get("newPublish", "type")
    destination = config.get("newPublish", "destination")
    
    if type == "FTP":
        #pathAndFile = join(local_dir, filename)
        #outputfile = open(pathAndFile, 'rb')
        # !! Need to cope with multiple files
        print "!! Needs work"
        #session = ftplib.FTP("ftp.%s"%destination)
        #password = getpass.getpass("Password?")
        #session.login(destination, password)
        #session.storbinary("STOR wwwroot\\%s"%filename, outputfile)
        #session.quit()     
        #outputfile.close()

        # !! Need to upload detail files as well
    elif type == "AWS":    
        s3 = boto.connect_s3()
        bucket = s3.get_bucket(destination)
        
        k = Key(bucket)
        print "Uploading:"

        templateFiles = [ f for f in listdir(local_dir) if isfile(join(local_dir,f)) ]
        for file in templateFiles:
            pathAndFile = join(local_dir, file)
            fileStream = open(pathAndFile, 'rb')
            k.key = file
            print file
            k.set_contents_from_file(fileStream)
            fileStream.close()

        detailPath = join(local_dir, DETAIL_DIR)
        detailFiles = [ f for f in listdir(detailPath) if isfile(join(detailPath,f)) ]
        for file in detailFiles:
            pathAndFile = join(detailPath, file)
            fileStream = open(pathAndFile, 'rb')
            k.key = posixpath.join(DETAIL_DIR, file)
            print file
            k.set_contents_from_file(fileStream)
            fileStream.close()
        
def display(filename):
    config = ConfigParser.ConfigParser({ "display" : "no"})
    config.readfp(open('portfolio.ini'))
    doDisplay = ("y" in config.get("newPublish", "display"))
    if doDisplay:
        webbrowser.open("http://www.%s/%s"%(DESTINATION, filename))

def writeCurrentDetail(history, portfolio, investments, ticker):
    directory = os.path.join(OUTPUT_DIR, DETAIL_DIR)
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    detailFile = open(os.path.join(directory, ticker+".html"), "w")
    
    detailFile.write("<TR><TD COLSPAN=\"2\"><B>%s</B></TD></TR>\n"%investments[ticker].fullname)
    boughtDates = portfolio.holdings[ticker].activeBoughtDates()
    if len(boughtDates) == 1:
        detailFile.write("<TR><TD>Bought</TD><TD>%s</TD></TR>\n"%boughtDates[0].strftime("%d %b %Y"))
        detailFile.write("<TR><TD>Holding period</TD><TD>%d days</TD></TR>\n"%portfolio.holdings[ticker].averageHoldingPeriod())
    else:
        detailFile.write("<TR><TD ROWSPAN='%d'>Bought</TD><TD>%s</TD></TR>\n"%(len(boughtDates), boughtDates[0].strftime("%d %b %Y")))
        for date in boughtDates[1:]:
            detailFile.write("<TR><TD>%s</TD></TR>\n"%date.strftime("%d %b %Y")) 
        detailFile.write("<TR><TD>Average holding period</TD><TD>%d days</TD></TR>\n"%portfolio.holdings[ticker].averageHoldingPeriod())

    initialDate = portfolio.holdings[ticker].firstBought()    
    for year in range(initialDate.year, datetime.today().year + 1):
        if year == initialDate.year:
            firstDate = initialDate
        else:        
            firstDate = datetime(year = year, month = 1, day = 1).date()
            
        if year == datetime.today().year:
            secondDate = datetime.today().date()
        else:
            secondDate = datetime(year = year + 1, month = 1, day = 1).date()
        
        firstPortfolio = history.getPortfolio(firstDate)
        secondPortfolio = history.getPortfolio(secondDate)
        
        profit = secondPortfolio.holdings[ticker].activeProfit() - firstPortfolio.holdings[ticker].activeProfit()
        percentProfit = profit / firstPortfolio.holdings[ticker].currentValue()
        
        detailFile.write("<TR><TD>%d Profit</TD><TD style='color:%s'>%.1f%%</TD></TR>\n"%(year, 'green' if percentProfit > 0 else 'red', percentProfit * 100))
    if investments[ticker].blogUrl:
        detailFile.write("<TR><TD COLSPAN=\"2\"><A HREF=\"%s\">Blog</A></TD></TR>\n"%investments[ticker].blogUrl)
    detailFile.close()
    
def writePreviousDetail(history, portfolio, investments, purchase):
    directory = os.path.join(OUTPUT_DIR, DETAIL_DIR)
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    detailFile = open(os.path.join(directory, purchase.uniqueId()+".html"), "w")
    
    detailFile.write("<TR><TD COLSPAN=\"2\"><B>%s</B></TD></TR>\n"%investments[purchase.ticker].fullname)
    detailFile.write("<TR><TD>Bought</TD><TD>%s</TD></TR>\n"%purchase.date_bought.strftime("%d %b %Y"))
    if len(purchase.date_sold) != 1:
        detailFile.write("<TR><TD ROWSPAN='%d'>Sold</TD><TD>%s</TD></TR>\n"%(len(purchase.date_sold),purchase.date_sold[0].strftime("%d %b %Y")))
        for date_sold in purchase.date_sold[1:]:
            detailFile.write("<TR><TD>%s</TD></TR>\n"%date_sold.strftime("%d %b %Y"))                    
    else:
        detailFile.write("<TR><TD>Sold</TD><TD>%s</TD></TR>\n"%purchase.date_sold[0].strftime("%d %b %Y"))
    profit = purchase.percent_profit()
    detailFile.write("<TR><TD>Profit</TD><TD style='color:%s'>%.1f%%</TD></TR>\n"%(
                     ("green" if profit > 0 else "red"), 
                     profit))
        
    # Annual profit
    profit = purchase.annual_profit()
    detailFile.write("<TR><TD>Annual profit</TD><TD style='color:%s'>%.1f%%</TD></TR>\n"%(
                     ("green" if profit > 0 else "red"), 
                     profit))
    
    if investments[purchase.ticker].blogUrl:
        detailFile.write("<TR><TD COLSPAN=\"2\"><A HREF=\"%s\">Blog</A></TD></TR>\n"%investments[purchase.ticker].blogUrl)
        
    detailFile.close()
    
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
  <TR VALIGN=TOP CLASS=\"clickable\">\
<TH"+MOUSEABLE+">Share</TH>\
<TH"+MOUSEABLE+">Ticker</TH>\
<TH"+MOUSEABLE+" TITLE=\"Percentage of portfolio value\">Percentage</TH>\
<TH"+MOUSEABLE+" TITLE=\"Average purchase price\">Bought at (p)</TH>\
<TH"+MOUSEABLE+" TITLE=\"Current price\">Current (p)</TH>\
<TH"+MOUSEABLE+" TITLE=\"Average per-share accumulated dividends received\">Dividends (p)</TH>\
<TH"+MOUSEABLE+" TITLE=\"Average per-share profit, including capital gain and dividends received\">Profit</TH>\
<TH"+MOUSEABLE+" TITLE=\"Average annual per-share profit, including capital gain and dividends received\">Annual profit</TH>\
</TR>\n")

    for ticker in sorted(portfolio.currentTickers(), key=lambda x: portfolio.holdings[x].value(), reverse = True):
        holding = portfolio.holdings[ticker]
        outputfile.write("  <TR CLASS=\"CLICKABLE\" VALIGN=TOP onClick=\"detail('%s')\" %s>"%(ticker, MOUSEABLE))
        
        writeCurrentDetail(history, portfolio, investments, ticker)
        
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
        outputfile.write("<TD style='color:%s'>%.1f%%</TD>"%(
                         ("green" if profit > 0 else "red"), 
                         profit))
        
        # Annual profit
        profit = 100 * ((1 + (holding.activeProfit() / holding.activeCost())) ** (365.0 / holding.averageHoldingPeriod()) - 1)
        outputfile.write("<TD><FONT COLOR=\"%s\">%.1f%%</FONT></TD>"%(
                         ("#008000" if profit > 0 else "#800000"), 
                         profit))
                         
        outputfile.write("\n")

    outputfile.write("</TABLE>\n")
    
def writePrevious(outputfile, history, portfolio, investments):
    outputfile.write("<B>Former holdings</B><BR>\n")
    outputfile.write(
"<TABLE WIDTH=100%% BORDER=1 BORDERCOLOR=\"#888888\" CELLPADDING=2 CELLSPACING=0 CLASS=\"sortable\" style=\"font-size:12px\">\n\
<TR VALIGN=TOP CLASS=\"clickable\">\n\
<TH"+MOUSEABLE+">Share</TH>\n\
<TH"+MOUSEABLE+">Ticker</TH>\n\
<TH"+MOUSEABLE+" TITLE=\"Average purchase price\">Bought at (p)</TH>\n\
<TH"+MOUSEABLE+" TITLE=\"Average sale price\">Sold at (p)</TH>\n\
<TH"+MOUSEABLE+" TITLE=\"Average per-share accumulated dividends received\">Dividends (p)</TH>\n\
<TH"+MOUSEABLE+" TITLE=\"Average per-share profit, including capital gain and dividends received\">Profit</TH>\n\
<TH"+MOUSEABLE+" TITLE=\"Average annual per-share profit, including capital gain and dividends received\">Annual profit</TH>\n\
</TR>\n")

    purchases = []
    for ticker, holding in portfolio.holdings.iteritems():
        purchases.extend(holding.inactivePurchases())
        
    purchases.sort(key=lambda x: x.percent_profit(), reverse = True)

    for purchase in purchases:
        outputfile.write("  <TR CLASS=\"CLICKABLE\" VALIGN=TOP onClick=\"detail('%s')\" %s>"%(purchase.uniqueId(), MOUSEABLE))

        writePreviousDetail(history, portfolio, investments, purchase)

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
        outputfile.write("<TD style='color:%s'>%.1f%%</TD>"%(
                         ("green" if profit > 0 else "red"), 
                         profit))
        
        # Annual profit
        profit = purchase.annual_profit()
        outputfile.write("<TD style='color:%s'>%.1f%%</TD>"%(
                         ("green" if profit > 0 else "red"), 
                         profit))
                         
        outputfile.write("\n")

    outputfile.write("</TABLE>\n")
    
def writeProfit(outputfile, history, portfolio, investments):
    global chartIndex

    outputfile.write("\
var data%d = google.visualization.arrayToDataTable([\n\
['Month', 'Profit'],\n"%chartIndex)
    
    totalDays = datetime.today().date() - history.startDate()
        
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
    backgroundColor: { fill: 'transparent' },\n\
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
    
    totalDays = datetime.today().date() - history.startDate()
    
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
    backgroundColor: { fill: 'transparent' },\n\
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
    
    totalDays = datetime.today().date() - history.startDate()
    
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
    backgroundColor: { fill: 'transparent' },\n\
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
    global chartIndex

    outputfile.write("\
var data%d = google.visualization.arrayToDataTable([\n\
['Sector', 'Percentage'],\n"%chartIndex)
    
    sectors = {}    
    for ticker in portfolio.currentTickers():
        sector = investments[ticker].sector
        if not sector in sectors:
            sectors[sector] = 0
        sectors[sector] += 100 * portfolio.holdings[ticker].value() / portfolio.totalValue()
        
    for sector in sectors:
        outputfile.write("['%s',%.1f],\n"%(
                         sector,
                         sectors[sector],
                         ))
    
    outputfile.write("]);\n\
\n\
  var options%d = {\n\
    title: 'Sectors',\n\
    legend: {position: 'none'},\n\
    pieSliceText: 'label',\n\
    backgroundColor: { fill: 'transparent' },\n\
  };\n\
\n\
  var chart%d = new google.visualization.PieChart(document.getElementById('chart_div%d'));\n\
\n\
  chart%d.draw(data%d, options%d);\n"%(chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex))
    chartIndex += 1
    
def writeClass(outputfile, history, portfolio, investments):
    global chartIndex

    outputfile.write("\
var data%d = google.visualization.arrayToDataTable([\n\
['Asset Class', 'Percentage'],\n"%chartIndex)
    
    classes = {}    
    for ticker in portfolio.currentTickers():
        assetClass = "%s %s"%(investments[ticker].region, investments[ticker].assetclass)
        if not assetClass in classes:
            classes[assetClass] = 0
        classes[assetClass] += 100 * portfolio.holdings[ticker].value() / portfolio.totalValue()
        
    for assetClass in classes:
        outputfile.write("['%s',%.1f],\n"%(
                         assetClass,
                         classes[assetClass],
                         ))
    
    outputfile.write("]);\n\
\n\
  var options%d = {\n\
    title: 'Asset classes',\n\
    legend: {position: 'none'},\n\
    pieSliceText: 'label',\n\
    backgroundColor: { fill: 'transparent' },\n\
  };\n\
\n\
  var chart%d = new google.visualization.PieChart(document.getElementById('chart_div%d'));\n\
\n\
  chart%d.draw(data%d, options%d);\n"%(chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex,
                                       chartIndex))
    chartIndex += 1
    
def writeDate(outputfile, history, portfolio, investments):
    outputfile.write("%s"%datetime.today().date())            
            
def writePrivateSummary(outputfile, history, portfolio, investments):
    outputfile.write(htmlOutput.portfolioSummary(portfolio))

def writePrivateCompare(outputfile, history, portfolio, investments):
    outputfile.write("<DIV style='font-weight:bold'>Performance</DIV><BR>\n")
    years = range(history.startDate().year, datetime.today().date().year + 1)
    outputfile.write("<TABLE><TR>\n")

    per_line = len(years) / (((len(years) - 1) / 8) + 1)
    split_in = per_line
    for year in years:
        if split_in == 0:
            split_in = per_line
            outputfile.write("</TR><TR>")
        outputfile.write("<TD><DIV class='yearlink' onClick=\"$('.year').hide();$('#%d').show();\">%d</DIV></TD>\n"%(year,year))
        split_in -= 1

    outputfile.write("</TR></TABLE><TABLE><TR>\n")
    outputfile.write("<TD><DIV class='yearlink' onClick=\"$('.year').hide();$('#90days').show();\">90 days</DIV></TD>\n")
    outputfile.write("<TD><DIV class='yearlink' onClick=\"$('.year').hide();$('#30days').show();\">30 days</DIV></TD>\n")
    outputfile.write("<TD><DIV class='yearlink' onClick=\"$('.year').hide();$('#7days').show();\">7 days</DIV></TD>\n")
    outputfile.write("<TD><DIV class='yearlink' onClick=\"$('.year').hide();$('#1days').show();\">Today</DIV></TD>\n")
    outputfile.write("</TR></TABLE><BR>\n")
    for year in years:
        if history.startDate().year == year:
            startDate = history.startDate()
        else:
            startDate = datetime(year=year, month=1, day=1).date()
        if year == datetime.today().date().year:
            endDate = datetime.today().date()
            outputfile.write("<DIV id='%d' class='year' style='margin-left: 30px;'><B>%d</B><BR>"%(year, year))
        else:
            endDate = datetime(year=year+1, month=1, day=1).date()
            outputfile.write("<DIV id='%d' class='year' style='display:none;margin-left: 30px;'><B>%d</B><BR>"%(year, year))
        outputfile.write(htmlOutput.portfolioDiff(startDate, endDate, history))
        outputfile.write("</DIV>")

    for day in (1,7,30,90):
        startDate = (datetime.today() - timedelta(days = day)).date()
        outputfile.write("<DIV id='%ddays' class='year' style='display:none;margin-left: 30px;'><B>%s</B><BR>"%(day, "Today" if (day == 1) else ("Last %d days"%day)))
        outputfile.write(htmlOutput.portfolioDiff(startDate, datetime.today().date(), history))
        outputfile.write("</DIV>")

def actionTemplate(history, portfolio, investments, template):
    global chartIndex
    
    # tag: (function, isScript, width)
    tags = {"###CURRENT###"      : (writeCurrent, False, 0),
            "###PREVIOUS###"     : (writePrevious, False, 0),
            "###PROFIT###"       : (writeProfit, True, 600),
            "###SIZE###"         : (writeSize, True, 600),
            "###NET###"          : (writeNet, True, 600),
            "###SECTOR###"       : (writeSector, True, 300),
            "###CLASS###"        : (writeClass, True, 300),
            "###DATE###"         : (writeDate, False ,0),
            "###PRIV_SUMMARY###" : (writePrivateSummary, False, 0),
            "###PRIV_COMPARE###" : (writePrivateCompare, False, 0),
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
            width = tags[line.strip()][2]
            style = ""
            if width < 600:
                style = " display: table-cell"
            outputfile.write("<div id=\"chart_div%d\" style=\"width: %dpx; height: 300px;%s\"></div>\n"%(writeTags[line.strip()], width, style))
        elif line.strip() in tags:
            tags[line.strip()][0](outputfile, history, portfolio, investments)
        else:
            outputfile.write(line)
    outputfile.close()
    
def mainPage(history, portfolio, investments):

    templateFiles = [ f for f in listdir(TEMPLATE_DIR) if isfile(join(TEMPLATE_DIR, f)) ]

    for template in templateFiles:
        actionTemplate(history, portfolio, investments, template)

    uploadAll()
    for template in templateFiles:
        display(template)
    
    
