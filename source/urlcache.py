import threading
import urllib.request, urllib.error, urllib.parse
import os
import time
import hashlib

class get_url (threading.Thread):

    def __init__ ( self, url, target, parent, lock):
        self.url = url
        self.target = target
        self.parent = parent
        self.lock = lock
        threading.Thread.__init__ ( self )

    def run(self):
        try:
            response = urllib.request.urlopen(self.url)
            html = response.read().decode("utf-8")
            if "Invalid API call" in html:
                time.sleep(60)
                response = urllib.request.urlopen(self.url)
                html = response.read()
        except Exception as err:
            print("Failed to open %s: %s"%(self.url, str(err)))
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
        indexfile = open("./cache/index.txt","w")
        for url in self.urls:
            num_urls = num_urls + 1
            str = "./cache/%s"%hashlib.sha224(url.encode("utf-8")).hexdigest()
            self.urlfile[url] = str
            get_url(url, self.urlfile[url], self, lock).start()
            indexfile.write("%s: %s\n"%(url, str))
        while self.counter < num_urls:
            time.sleep(1)

    def read_url(self, url):
        cached_file = open(self.urlfile[url], 'r')
        html = cached_file.read()
        return html

    def clean_urls(self):
        for url in self.urls:
            os.remove(self.urlfile[url])

