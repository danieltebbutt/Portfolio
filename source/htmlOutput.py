#
# All output to screen
#
import transaction
import holding
import purchase
import datetime

class htmlOutput:

    @staticmethod
    def income(transactions):
        dividends = 0.0
        print "%-45s %-9s"%("Transactions:", "Cumulative dividends:")
        for transaction in transactions:
            if transaction.action == "EXDIV":
                dividends += transaction.price * transaction.number / 100
                print u"%-45s \N{pound sign}%-8.2f"%(transaction.description(), dividends)
        print

    @staticmethod
    def portfolioSummary(portfolio):
        output = ""
        output += "<B>Summary</B> (%s)<BR>\n"%datetime.datetime.today().date()
        output += "<BR>\n"
        output += "<TABLE>\n"
        output += "<TR><TH>Number</TH><TH>Ticker</TH><TH>Cost</TH><TH>Value</TH><TH>Dividends</TH><TH>Profit</TH></TR>"
    
        for holding in portfolio.holdings.values():
            if holding.number != 0:
                output += "<TR><TD>%s</TD><TD>%d</TD><TD>&pound;%.2f</TD><TD>&pound;%.2f</TD><TD>&pound;%.2f</TD><TD class='num'>&pound;%.2f</TD></TR>"%(\
                    holding.ticker,
                    holding.number,
                    holding.activeCost() / 100,
                    holding.currentValue() / 100,
                    holding.totalDividends() / 100, 
                    holding.activeProfit() / 100)
        output += "</TABLE>\n"
        output += "<BR>\n"
        output += "<TABLE>\n"
        output += "<TR><TD>Net invested</TD><TD>&pound;%.2f</TD></TR>\n"%(portfolio.netInvested() / 100)
        output += "<TR><TD>Current value</TD><TD>&pound;%.2f</TD></TR>\n"%(portfolio.value() / 100)
        output += "<TR><TD>Profit</TD><TD class='num'>&pound;%.2f</TD></TR>\n"%(portfolio.totalProfit() / 100)
        output += "</TABLE>\n"
        output += "<BR>\n"
        return output
        
    @staticmethod
    def portfolioPurchases(portfolio):
        print "Ranked purchases:"
        purchases = []
        for holding in portfolio.holdings.values():
            purchases.extend(holding.purchases)
        for purchase in reversed(sorted(purchases, key=lambda purchase: purchase.percent_profit())):
            print purchase.toString()
        print
        
    @staticmethod
    def portfolioDiff(startDate, endDate, history):     
        output=""
   
        startPortfolio = history.getPortfolio(startDate)
        endPortfolio = history.getPortfolio(endDate)
        # Print some other stuff
       
        totalProfit = (endPortfolio.totalProfit() - startPortfolio.totalProfit()) / 100
        basisForReturn = history.basisForReturn(startDate, endDate) / 100
        output += "<TABLE>\n"
        output += "<TR class='returnCalc' style='display:none'><TD>Start value</TD><TD>&pound;%.2f</TD></TR>\n"%(startPortfolio.value() / 100)
        output += "<TR class='returnCalc' style='display:none'><TD>End value</TD><TD>&pound;%.2f</TD></TR>\n"%(endPortfolio.value() / 100)
        output += "<TR class='returnCalc' style='display:none'><TD>Basis for return</TD><TD>&pound;%.2f</TD></TR>\n"%(basisForReturn)
        output += "<TR style='font-weight:bold' class='clickableUnderline' onClick='$(\".returnCalc\").toggle();'><TD>Return</TD><TD class='num'>%.2f%%</TD></TR>\n"%(100 * totalProfit / basisForReturn)
        output += "</TABLE>\n"
        output += "<BR>\n"
        output += "<TABLE>\n"
        output += "<TR><TH>Ticker</TH><TH>Capital Gain</TH><TH>Dividends</TH><TH>Total</TH></TR>"
        # Print a line for each holding 
        for ticker, endHolding in endPortfolio.holdings.iteritems():
            startHolding = None
            if ticker in startPortfolio.holdings:
                startHolding = startPortfolio.holdings[ticker]
                
            if not startHolding:
                startProfit = 0
                startCapitalGain = 0
                startTotalDividends = 0
            elif startHolding.profit() != endHolding.profit() or startHolding.number != 0 or endHolding.number != 0:
                startProfit = startHolding.profit()
                startCapitalGain = startHolding.capitalGain()
                startTotalDividends = startHolding.totalDividends()
            else:
                startProfit = None
                
            if startProfit != None:
                output += "<TR><TD>%s</TD><TD class='num'>&pound;%.2f</TD><TD class='num'>&pound;%.2f</TD><TD class='num'>&pound;%.2f</TD></TR>"%(
                      ticker,
                      (endHolding.capitalGain() - startCapitalGain) / 100,
                      (endHolding.totalDividends() - startTotalDividends) / 100,
                      (endHolding.profit() - startProfit) / 100)
        output += "<TR style='font-weight:bold'><B>\n"
        output += "<TD>Total</TD>\n"
        output += "<TD class='num'>&pound;%.2f</TD>\n"%((endPortfolio.capitalGain() - startPortfolio.capitalGain()) / 100)
        output += "<TD class='num'>&pound;%.2f</TD>\n"%((endPortfolio.totalDividends() - startPortfolio.totalDividends()) / 100)
        output += "<TD class='num'>&pound;%.2f</TD>\n"%(totalProfit)
        output += "</TR>"
        output += "</TABLE>\n"

        return output
        
    @staticmethod
    def capitalGain(portfolio):
        purchases = []
        for holding in portfolio.holdings.values():
            purchases.extend(holding.activePurchases())
        gain = 0
        loss = 0
        for purchase in purchases:
            print u"%6s \N{pound sign}%9.2f"%(purchase.ticker, purchase.capitalGain() / 100)
            if purchase.capitalGain() > 0:
                gain += purchase.capitalGain() / 100
            else:
                loss += purchase.capitalGain() / 100
        print
        print u"Gain   \N{pound sign}%9.2f"%(gain)
        print u"Loss   \N{pound sign}%9.2f"%(loss)
        
    @staticmethod
    def tax(history, investments, year):
        # For all shares held on 1st January after year end, print purchase info and dividends received        
        endDate = datetime.date(year = year + 1, month = 1, day = 1)
        endPortfolio = history.getPortfolio(endDate)
        endExchangeRate = history.price("NOK", endDate)
                
        startDate = datetime.date(year = year, month = 1, day = 1)
        startPortfolio = history.getPortfolio(startDate)
        startExchangeRate = history.price("NOK", startDate)
        
        for ticker in history.activeTickers(startDate, endDate):
            holding = endPortfolio.holdings[ticker]
            print
            print "%s - %s"%(ticker, investments[ticker].isin)
            if startPortfolio.contains(ticker):
                startHolding = startPortfolio.holdings[ticker]
                print "At year start: %d @ %.6f = %.6f NOK"%(startHolding.number, startHolding.price / startExchangeRate, (startHolding.number * startHolding.price / startExchangeRate))
            if endPortfolio.contains(ticker):
                print "At year end:   %d @ %.6f = %.6f NOK"%(holding.number, holding.price / endExchangeRate, (holding.number * holding.price / endExchangeRate))
            print "Transactions:"
            for transaction in history.getTransactions(None, endDate, ticker, ["BUY","SELL","RIGHTS","SCRIP"]):
                print "%s %s %d @ %.6f = %.6f NOK"%(transaction.date, 
                                                    transaction.action, 
                                                    transaction.number, 
                                                    ((transaction.price + (transaction.comm / transaction.number)) / history.price("NOK", transaction.date)),
                                                    (transaction.number * transaction.price + transaction.comm) / history.price("NOK", transaction.date))
                
            print "Dividends:"
            dividends = history.getTransactions(startDate, endDate, ticker, "DIV")            
            if dividends:
                totalPerShare = 0
                total = 0
                for transaction in dividends:
                    perShare = transaction.price / (history.price("NOK", transaction.date))
                    dividend = (transaction.number * transaction.price) / (history.price("NOK", transaction.date))
                    print "%s %d @ %.6f = %.6f NOK"%(transaction.date, transaction.number, perShare, dividend)
                    totalPerShare += perShare
                    total += dividend
                print " @ %.6f = %.6f NOK"%(totalPerShare, total)
            else:
                print "(None)"
        print
        print "Total dividends for the year = %.6f NOK"%history.dividendsReceived(startDate, endDate, "NOK")
    
    @staticmethod
    def portfolioYield(portfolio, investments):
        totalDividends = 0
        for ticker in portfolio.currentTickers():
            shareYield = investments[ticker].estdivi / portfolio.holdings[ticker].price
            totalDividends += investments[ticker].estdivi * portfolio.holdings[ticker].number
            print "%9s estimated yield: %.2f%%"%(ticker, shareYield * 100)
        print u"Portfolio estimated yield: %.2f%% (\N{pound sign}%.0f)"%((100 * totalDividends / portfolio.value()), totalDividends / 100)
        
    @staticmethod
    def transactions(transactions):
        for transaction in transactions:
            print transaction.toString()    
    
    @staticmethod
    def shareInfo(history, ticker, startDate, endDate):
        print u"%-14s %-10s %-6s %-10s"%("Date", "Price", "Number", "Value")
        for price in sorted(history.prices):
            if price[0] == ticker and price[1] >= startDate and price[1] <= endDate:
                holding = history.getPortfolio(price[1]).holdings[ticker]
                print u"%-14s %-10.2f %-6d \N{pound sign}%-10.2f"%(price[1], history.prices[price], holding.number, holding.value() / 100)
        
        
