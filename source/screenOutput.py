#
# All output to screen
#
import transaction
import holding
import portfolio
import purchase

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