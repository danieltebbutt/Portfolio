class get_url (threading.Thread):

    def __init__ ( self, stocks, verbose, porty, lock):
        self.stocks = stocks
        self.verbose = verbose
        self.porty = porty
        self.lock = lock
        lock.acquire()
        lock.release()
        threading.Thread.__init__ ( self )

    def run(self):
        self.get_share_price_history(self.stocks)
        self.lock.acquire()
        self.porty.threads_complete = self.porty.threads_complete + 1
        self.lock.release()

    def get_share_price_history(self, stocks):
        for stock, url in stocks:
            if self.verbose:
                print("Getting info for %s..."%(stock))
            try:
                response = urllib.request.urlopen(url)
                html = response.read()
                for daysdata in YAHOODAY.findall(html):
                    date=daysdata[0]
                    closeprice=float(daysdata[4])
                    stockdate = datetime.date(int(YAHOODATE.match(date).group('year')), \
                                              int(YAHOODATE.match(date).group('month')), \
                                              int(YAHOODATE.match(date).group('day')))
                    self.lock.acquire()
                    self.porty.history[stockdate].note_price(stock, closeprice)
                    self.lock.release()
            except Exception as err:
                print("Failed to open %s %s"%(url, err))
            if self.verbose:
                print("Info complete for %s..."%stock)
