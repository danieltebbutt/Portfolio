# Web publishing
import os
import webbrowser
import ftplib
import getpass
import pathlib
import io
from os import listdir
from os.path import isfile, join
from datetime import timedelta
from datetime import datetime
from datetime import date as datelib
import posixpath
from abc import ABCMeta, abstractmethod
import configparser

from .htmlOutput import *

class publisher(object):

    TEMPLATE_DIR = pathlib.Path(__file__).parent.parent /  'templates'
    MOUSEABLE = " onmouseover=\"this.style.background='lightgray'\" onmouseout=\"this.style.background='';\""

    chartIndex = 1

    def __init__(self, history, portfolio, investments):
        self.history = history
        self.portfolio = portfolio
        self.investments = investments
            
    def display(self, filename):
        config = configparser.ConfigParser({ "display" : "no"})
        config.readfp(open('portfolio.ini'))
        doDisplay = ("y" in config.get("newPublish", "display"))
        if doDisplay:
            webbrowser.open("http://www.%s/%s"%(DESTINATION, filename))

    def writeCurrentDetail(self, ticker):
        filename = ticker+".html"
        detailFile = self.openDetailFile(filename)

        detailFile.write("<TR><TD COLSPAN=\"2\"><B>%s</B></TD></TR>\n"%self.investments[ticker].fullname)
        boughtDates = self.portfolio.holdings[ticker].activeBoughtDates()
        if len(boughtDates) == 1:
            detailFile.write("<TR><TD>Bought</TD><TD>%s</TD></TR>\n"%boughtDates[0].strftime("%d %b %Y"))
            detailFile.write("<TR><TD>Holding period</TD><TD>%d days</TD></TR>\n"%self.portfolio.holdings[ticker].averageHoldingPeriod())
        else:
            detailFile.write("<TR><TD ROWSPAN='%d'>Bought</TD><TD>%s</TD></TR>\n"%(len(boughtDates), boughtDates[0].strftime("%d %b %Y")))
            for date in boughtDates[1:]:
                detailFile.write("<TR><TD>%s</TD></TR>\n"%date.strftime("%d %b %Y")) 
            detailFile.write("<TR><TD>Average holding period</TD><TD>%d days</TD></TR>\n"%self.portfolio.holdings[ticker].averageHoldingPeriod())

        initialDate = self.portfolio.holdings[ticker].firstBought()    
        for year in range(initialDate.year, datelib.today().year + 1):
            if year == initialDate.year:
                firstDate = initialDate
            else:        
                firstDate = datetime.date(year = year, month = 1, day = 1)
                
            if year == datelib.today().year:
                secondDate = datelib.today()
            else:
                secondDate = datetime.date(year = year + 1, month = 1, day = 1)
            
            firstPortfolio = self.history.getPortfolio(firstDate)
            secondPortfolio = self.history.getPortfolio(secondDate)
            
            profit = secondPortfolio.holdings[ticker].activeProfit() - firstPortfolio.holdings[ticker].activeProfit()
            percentProfit = profit / firstPortfolio.holdings[ticker].currentValue()
            
            detailFile.write("<TR><TD>%d Profit</TD><TD style='color:%s'>%.1f%%</TD></TR>\n"%(year, 'green' if percentProfit > 0 else 'red', percentProfit * 100))
        if self.investments[ticker].blogUrl:
            detailFile.write("<TR><TD COLSPAN=\"2\"><A HREF=\"%s\">Blog</A></TD></TR>\n"%self.investments[ticker].blogUrl)

        self.closeDetailFile(detailFile, filename)
        
    @abstractmethod
    def openDetailFile(self, filename):
        pass

    @abstractmethod
    def closeDetailFile(self, detailFile, filename):
        pass

    def writePreviousDetail(self, purchase):
        filename = purchase.uniqueId()+".html"
        detailFile = self.openDetailFile(filename)

        detailFile.write("<TR><TD COLSPAN=\"2\"><B>%s</B></TD></TR>\n"%self.investments[purchase.ticker].fullname)
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
        
        if self.investments[purchase.ticker].blogUrl:
            detailFile.write("<TR><TD COLSPAN=\"2\"><A HREF=\"%s\">Blog</A></TD></TR>\n"%self.investments[purchase.ticker].blogUrl)
            
        self.closeDetailFile(detailFile, filename)
        
    def writeScriptHeader(self, outputfile):
        outputfile.write("\
    <script type=\"text/javascript\" src=\"https://www.google.com/jsapi\"></script>\n\
    <script type=\"text/javascript\">\n\
    google.load(\"visualization\", \"1\", {packages:[\"corechart\"]});\n\
    google.setOnLoadCallback(drawChart);\n\
    function drawChart() {\n")

    def writeScriptFooter(self, outputfile):
        outputfile.write("\
    }\n\
    </script>\n")

    def writeCurrent(self, outputfile):
        outputfile.write("<DIV ALIGN=\"Left\"><B>Current portfolio (%d%% of peak size)</B><BR></DIV>\n"%(self.portfolio.value() * 100 / self.history.peakValue()))

        outputfile.write(
    "<TABLE WIDTH=100%% BORDER=1 BORDERCOLOR=\"#888888\" CELLPADDING=2 CELLSPACING=0 CLASS=\"sortable\" style=\"font-size:12px\">\n\
    <TR VALIGN=TOP CLASS=\"clickable\">\
    <TH"+self.MOUSEABLE+">Share</TH>\
    <TH"+self.MOUSEABLE+">Ticker</TH>\
    <TH"+self.MOUSEABLE+" TITLE=\"Percentage of portfolio value\">Percentage</TH>\
    <TH"+self.MOUSEABLE+" TITLE=\"Average purchase price\">Bought at (p)</TH>\
    <TH"+self.MOUSEABLE+" TITLE=\"Current price\">Current (p)</TH>\
    <TH"+self.MOUSEABLE+" TITLE=\"Average per-share accumulated dividends received\">Dividends (p)</TH>\
    <TH"+self.MOUSEABLE+" TITLE=\"Average per-share profit, including capital gain and dividends received\">Profit</TH>\
    <TH"+self.MOUSEABLE+" TITLE=\"Average annual per-share profit, including capital gain and dividends received\">Annual profit</TH>\
    </TR>\n")

        for ticker in sorted(self.portfolio.currentTickers(), key=lambda x: self.portfolio.holdings[x].value(), reverse = True):
            holding = self.portfolio.holdings[ticker]
            outputfile.write("  <TR CLASS=\"CLICKABLE\" VALIGN=TOP onClick=\"detail('%s')\" %s>"%(ticker, self.MOUSEABLE))
            
            self.writeCurrentDetail(ticker)
            
            # Full name
            outputfile.write("<TD>%s</TD>"%self.investments[ticker].fullname)
            
            # Ticker
            outputfile.write("<TD>%s</TD>"%ticker)
            
            # Percentage of total value
            outputfile.write("<TD>%.1f%%"%(100 * holding.value() / self.portfolio.value()))
            
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
            if holding.averageHoldingPeriod() == 0:
                profit = 0
            else:
                profit = 100 * ((1 + (holding.activeProfit() / holding.activeCost())) ** (365.0 / holding.averageHoldingPeriod()) - 1)
            outputfile.write("<TD><FONT COLOR=\"%s\">%.1f%%</FONT></TD>"%(
                            ("#008000" if profit > 0 else "#800000"), 
                            profit))
                            
            outputfile.write("\n")

        outputfile.write("</TABLE>\n")
        
    def writePrevious(self, outputfile):
        outputfile.write("<B>Former holdings</B><BR>\n")
        outputfile.write(
    "<TABLE WIDTH=100%% BORDER=1 BORDERCOLOR=\"#888888\" CELLPADDING=2 CELLSPACING=0 CLASS=\"sortable\" style=\"font-size:12px\">\n\
    <TR VALIGN=TOP CLASS=\"clickable\">\n\
    <TH"+self.MOUSEABLE+">Share</TH>\n\
    <TH"+self.MOUSEABLE+">Ticker</TH>\n\
    <TH"+self.MOUSEABLE+" TITLE=\"Average purchase price\">Bought at (p)</TH>\n\
    <TH"+self.MOUSEABLE+" TITLE=\"Average sale price\">Sold at (p)</TH>\n\
    <TH"+self.MOUSEABLE+" TITLE=\"Average per-share accumulated dividends received\">Dividends (p)</TH>\n\
    <TH"+self.MOUSEABLE+" TITLE=\"Average per-share profit, including capital gain and dividends received\">Profit</TH>\n\
    <TH"+self.MOUSEABLE+" TITLE=\"Average annual per-share profit, including capital gain and dividends received\">Annual profit</TH>\n\
    </TR>\n")

        purchases = []
        for ticker, holding in self.portfolio.holdings.items():
            purchases.extend(holding.inactivePurchases())
            
        purchases.sort(key=lambda x: x.percent_profit(), reverse = True)

        for purchase in purchases:
            outputfile.write("  <TR CLASS=\"CLICKABLE\" VALIGN=TOP onClick=\"detail('%s')\" %s>"%(purchase.uniqueId(), self.MOUSEABLE))

            self.writePreviousDetail(purchase)

            # Full name
            outputfile.write("<TD>%s</TD>"%self.investments[purchase.ticker].fullname)
            
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
        
    def writeProfit(self, outputfile):
        global chartIndex

        outputfile.write("\
    var data%d = google.visualization.arrayToDataTable([\n\
    ['Month', 'Profit'],\n"%chartIndex)
        
        totalDays = datelib.today() - self.history.startDate()
            
        peakInvested = self.history.peakInvested()
        for days in range(0, totalDays.days, 28):
            date = self.history.startDate() + timedelta(days = days)
            outputfile.write("[new Date(%d,%d,%d),%.1f],\n"%(
                            date.year,
                            date.month - 1,
                            date.day,
                            100 * self.history.getPortfolio(date).totalProfit() / peakInvested
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
        
    def writeSize(self, outputfile):
        global chartIndex

        outputfile.write("\
    var data%d = google.visualization.arrayToDataTable([\n\
    ['Month', 'Size'],\n"%chartIndex)
        
        totalDays = datelib.today() - self.history.startDate()
        
        peakValue = self.history.peakValue()
        for days in range(0, totalDays.days, 28):
            date = self.history.startDate() + timedelta(days = days)
            outputfile.write("[new Date(%d,%d,%d),%.1f],\n"%(
                            date.year,
                            date.month - 1,
                            date.day,
                            100 * self.history.getPortfolio(date).totalValue() / peakValue
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
        
    def writeNet(self, outputfile):
        global chartIndex

        outputfile.write("\
    var data%d = google.visualization.arrayToDataTable([\n\
    ['Month', 'Size', 'Net invested'],\n"%chartIndex)
        
        totalDays = datelib.today() - self.history.startDate()
        
        peakValue = self.history.peakValue()
        for days in range(0, totalDays.days, 28):
            date = self.history.startDate() + timedelta(days = days)
            outputfile.write("[new Date(%d,%d,%d),%.1f,%.1f],\n"%(
                            date.year,
                            date.month - 1,
                            date.day,
                            100 * self.history.getPortfolio(date).totalValue() / peakValue,
                            100 * self.history.getPortfolio(date).netInvested() / peakValue
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
        
    def writeSector(self, outputfile):
        global chartIndex

        outputfile.write("\
    var data%d = google.visualization.arrayToDataTable([\n\
    ['Sector', 'Percentage'],\n"%chartIndex)
        
        sectors = {}    
        for ticker in self.portfolio.currentTickers():
            sector = self.investments[ticker].sector
            if not sector in sectors:
                sectors[sector] = 0
            sectors[sector] += 100 * self.portfolio.holdings[ticker].value() / self.portfolio.totalValue()
            
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
        
    def writeClass(self, outputfile):
        global chartIndex

        outputfile.write("\
    var data%d = google.visualization.arrayToDataTable([\n\
    ['Asset Class', 'Percentage'],\n"%chartIndex)
        
        classes = {}    
        for ticker in self.portfolio.currentTickers():
            assetClass = "%s %s"%(self.investments[ticker].region, self.investments[ticker].assetclass)
            if not assetClass in classes:
                classes[assetClass] = 0
            classes[assetClass] += 100 * self.portfolio.holdings[ticker].value() / self.portfolio.totalValue()
            
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
        
    def writeDate(self, outputfile):
        outputfile.write("%s"%datelib.today())            
                
    def writePrivateSummary(self, outputfile):
        outputfile.write(htmlOutput.portfolioSummary(self.portfolio))

    def writePrivateCompare(self, outputfile):
        outputfile.write("<DIV style='font-weight:bold'>Performance</DIV><BR>\n")
        years = list(range(self.history.startDate().year, datelib.today().year + 1))
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
            if self.history.startDate().year == year:
                startDate = self.history.startDate()
            else:
                startDate = datetime.date(year=year, month=1, day=1)
            if year == datelib.today().year:
                endDate = datelib.today()
                outputfile.write("<DIV id='%d' class='year' style='margin-left: 30px;'><B>%d</B><BR>"%(year, year))
            else:
                endDate = datetime.date(year=year+1, month=1, day=1)
                outputfile.write("<DIV id='%d' class='year' style='display:none;margin-left: 30px;'><B>%d</B><BR>"%(year, year))
            outputfile.write(htmlOutput.portfolioDiff(startDate, endDate, self.history))
            outputfile.write("</DIV>")

        for day in (1,7,30,90):
            try:
                startDate = (datelib.today() - timedelta(days = day))
                outputfile.write("<DIV id='%ddays' class='year' style='display:none;margin-left: 30px;'><B>%s</B><BR>"%(day, "Today" if (day == 1) else ("Last %d days"%day)))
                outputfile.write(htmlOutput.portfolioDiff(startDate, datelib.today(), self.history))
                outputfile.write("</DIV>")
            except:
                print("Error comparing vs %d days ago"%day)

    def actionTemplate(self, template, outputStream):
        global chartIndex
        
        # tag: (function, isScript, width)
        tags = {"###CURRENT###"      : (self.writeCurrent, False, 0),
                "###PREVIOUS###"     : (self.writePrevious, False, 0),
                "###PROFIT###"       : (self.writeProfit, True, 600),
                "###SIZE###"         : (self.writeSize, True, 600),
                "###NET###"          : (self.writeNet, True, 600),
                "###SECTOR###"       : (self.writeSector, True, 300),
                "###CLASS###"        : (self.writeClass, True, 300),
                "###DATE###"         : (self.writeDate, False ,0),
                "###PRIV_SUMMARY###" : (self.writePrivateSummary, False, 0),
                "###PRIV_COMPARE###" : (self.writePrivateCompare, False, 0),
                }

        fileStream = open(join(self.TEMPLATE_DIR,template), 'r')

        writeTags = {}
        chartIndex = 1

        for line in fileStream:
            if line.strip() in tags and tags[line.strip()][1]:
                writeTags[line.strip()] = 0

        fileStream.seek(0)

        for line in fileStream:
            if "</head>" in line.lower():
                if len(writeTags) > 0:
                    self.writeScriptHeader(outputStream)
                    for tag in writeTags:
                        writeTags[tag] = chartIndex
                        tags[tag][0](outputStream)
                    self.writeScriptFooter(outputStream)
                outputStream.write(line)
            elif line.strip() in writeTags:
                width = tags[line.strip()][2]
                style = ""
                if width < 600:
                    style = " display: table-cell"
                outputStream.write("<div id=\"chart_div%d\" style=\"width: %dpx; height: 300px;%s\"></div>\n"%(writeTags[line.strip()], width, style))
            elif line.strip() in tags:
                tags[line.strip()][0](outputStream)
            else:
                outputStream.write(line)
        
    @abstractmethod
    def mainPage():
        pass