#
# All output to screen
#
import transaction
import holding
import portfolio
import purchase
import datetime

class screenOutput:
    #
    # PRINTING FUNCTIONS
    #
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
        print "Portfolio summary (%s):"%portfolio.date
        for holding in portfolio.holdings.values():
            if holding.number != 0:              
                print holding.toStringActive()
        print u"Net invested:  \N{pound sign}%.2f"%(portfolio.netInvested() / 100)
        print u"Current value: \N{pound sign}%.2f"%(portfolio.value() / 100)
        print

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
        startPortfolio = history.getPortfolio(startDate)
        endPortfolio = history.getPortfolio(endDate)
    
        # Print a line for each holding 
        for ticker, endHolding in endPortfolio.holdings.iteritems():
            startHolding = None
            if ticker in startPortfolio.holdings:
                startHolding = startPortfolio.holdings[ticker]
                
            if not startHolding:
                startProfit = 0
            elif startHolding.profit() != endHolding.profit() or startHolding.number != 0 or endHolding.number != 0:
                startProfit = startHolding.profit()
            else:
                startProfit = None
                
            if startProfit != None:
                print u"%6s Capital: \N{pound sign}%8.2f Earnings: \N{pound sign}%8.2f Total: \N{pound sign}%8.2f"%(
                      ticker,
                      (endHolding.capitalGain() - startHolding.capitalGain()) / 100,
                      (endHolding.totalDividends() - startHolding.totalDividends()) / 100,
                      (endHolding.profit() - startProfit) / 100)
        print

        # Print some other stuff
        print u"Total capital:  \N{pound sign}%8.2f"%((endPortfolio.capitalGain() - startPortfolio.capitalGain()) / 100)
        print u"Total earnings: \N{pound sign}%8.2f"%((endPortfolio.totalDividends() - startPortfolio.totalDividends()) / 100)
        totalProfit = (endPortfolio.totalProfit() - startPortfolio.totalProfit()) / 100
        print u"Total profit:   \N{pound sign}%8.2f"%(totalProfit)
        print
        print u"Portfolio value at start of period: \N{pound sign}%.2f"%(startPortfolio.value() / 100)
        print u"Portfolio value at end of period: \N{pound sign}%.2f"%(endPortfolio.value() / 100)
        
        basisForReturn = history.basisForReturn(startDate, endDate) / 100
        print u"Basis for return: \N{pound sign}%.2f"%(basisForReturn)
        print u"Percentage return on investment: %.2f%%"%(100 * totalProfit / basisForReturn)
        
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
    