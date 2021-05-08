# Web publishing
import io
from os import listdir
from os.path import isfile, join

from .publisher import publisher

class azurePublisher(publisher):

    def __init__(self, history, portfolio, investments):
        self.details = []
        publisher.__init__(self, history, portfolio, investments)

    def openDetailFile(self, filename):
        detailFile = io.StringIO()  
        return detailFile

    def closeDetailFile(self, detailFile, filename):
        self.details.append(("portfolio/"+filename, detailFile.getvalue()))

    def mainPage(self):
        templateFiles = [ f for f in listdir(self.TEMPLATE_DIR) if isfile(join(self.TEMPLATE_DIR, f)) ]
        pages = []

        for template in templateFiles:
            outputStream = io.StringIO()
            self.actionTemplate(template, outputStream)
            pages.append((template, outputStream.getvalue()))

        return pages+self.details
