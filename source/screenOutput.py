#
# All output to screen
#
import transaction

class screenOutput:
    #
    # PRINTING FUNCTIONS
    #
    @staticmethod
    def printIncome(transactions):
        dividends = 0.0
        print "%-45s %-9s"%("Transactions:", "Divis:")
        for transaction in transactions:
            if transaction.action == "EXDIV":
                dividends += transaction.price * transaction.number / 100
                print u"%-45s \N{pound sign}%-8.2f"%(transaction.description(), dividends)
        print

