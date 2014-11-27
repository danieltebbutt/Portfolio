# Tracing

class trace:

    enabled = False

    @staticmethod
    def prt( str ):
        if trace.enabled:
            print str

    @staticmethod
    def enable():
        trace.enabled = True

    @staticmethod
    def disable():
        trace.enabled = False
