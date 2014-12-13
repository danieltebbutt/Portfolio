import threading
import urllib2
import os
import time

class get_url (threading.Thread):

    def __init__ ( self, url, target, parent, lock):
        self.url = url
        self.target = target
        self.parent = parent
        self.lock = lock
        threading.Thread.__init__ ( self )

    def run(self):
        try:
            response = urllib2.urlopen(self.url)
            html = response.read()
        except Exception, err:
            print "Failed to open %s: %s"%(self.url, str(err))
            html = ""
        outputfile = open(self.target, 'w') 
        outputfile.write(html)
        self.lock.acquire()
        self.parent.counter = self.parent.counter + 1
        self.lock.release()

class urlcache:

    def __init__(self, urls):
        self.urls = urls
        
    def add_url(self, url):
        self.urls.append(url)

    def cache_urls(self):
        lock = threading.Lock()
        self.counter = 0
        num_urls = 0
        self.urlfile = {}
        for url in self.urls:
            num_urls = num_urls + 1
            str = ".\\tmpfile%d"%num_urls
            self.urlfile[url] = str
            get_url(url, self.urlfile[url], self, lock).start()
        while self.counter < num_urls:
            time.sleep(1)

    def read_url(self, url):
        cached_file = open(self.urlfile[url], 'r')
        html = cached_file.read()
        return html

    def clean_urls(self):
        for url in self.urls:
            os.remove(self.urlfile[url])

