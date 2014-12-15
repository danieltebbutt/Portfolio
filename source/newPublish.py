# Web publishing

import os
import webbrowser
from os import listdir
from os.path import isfile, join
from datetime import timedelta
from datetime import datetime

TEMPLATE_DIR = ".\\templates"
OUTPUT_DIR = ".\\output"
DESTINATION = "danieltebbutt.com"

chartIndex = 1

def upload(filename):
    outputfile = open("%s\\%s"%(OUTPUT_DIR, filename), 'rb')

    session = ftplib.FTP("ftp.%s"%DESTINATION)
    password = getpass.getpass("Password?")
    session.login(DESTINATION, password)
    session.storbinary("STOR wwwroot\\%s"%filename, outputfile)
    outputfile.close()
    session.quit()
    
def display():
    webbrowser.open("http://www.%s/%s"%(DESTINATION, FILENAME))

def writeScriptHeader(outputfile):
    outputfile.write("\
<script type=\"text/javascript\" src=\"https://www.google.com/jsapi\"></script>\n\
<script type=\"text/javascript\">\n\
  google.load(\"visualization\", \"1\", {packages:[\"corechart\"]});\n\
google.setOnLoadCallback(drawChart);\n\
function drawChart() {\n")

def writeScriptFooter(outputfile):
    outputfile.write("\
}\n\
</script>\n")

def writeCurrent(outputfile, portfolio):
    outputfile.write("Test 1<BR>\n")
    
def writePrevious(outputfile, portfolio):
    outputfile.write("Test 2<BR>\n")
    
def writeProfit(outputfile, portfolio):
    outputfile.write("Test 3<BR>\n")
    
def writeSize(outputfile, portfolio):
    outputfile.write("Test 4<BR>\n")
    
def writeNet(outputfile, portfolio):
    outputfile.write("Test 5<BR>\n")
    
def writeSector(outputfile, portfolio):
    outputfile.write("Test 6<BR>\n")
    
def writeClass(outputfile, portfolio):
    outputfile.write("Test 7<BR>\n")
            
def actionTemplate(portfolio, template):

    # tag: (function, isScript)
    tags = {"###CURRENT###"      : (writeCurrent, False),
            "###PREVIOUS###"     : (writePrevious, False),
            "###PROFIT###"       : (writeProfit, True),
            "###SIZE###"         : (writeSize, True),
            "###NET###"          : (writeNet, True),
            "###SECTOR###"       : (writeSector, True),
            "###CLASS###"        : (writeClass, True),
            }

    fileStream = open(join(TEMPLATE_DIR,template), 'r')
    outputfile = open(join(OUTPUT_DIR,template), 'w')

    writeTags = {}
    chartIndex = 1

    for line in fileStream:
        if line.strip() in tags and tags[line.strip()][1]:
            writeTags[line.strip()] = 0

    fileStream.seek(0)

    for line in fileStream:
        if "</head>" in line.lower():
            if len(writeTags) > 0:
                writeScriptHeader(outputfile)
                for tag in writeTags:
                    writeTags[tag] = chartIndex
                    tags[tag][0](outputfile, portfolio)
                writeScriptFooter(outputfile)
            outputfile.write(line)
        elif line.strip() in writeTags:
            outputfile.write("<div id=\"chart_div%d\" style=\"width: 900px; height: 500px;\"></div>\n"%writeTags[tag])
        elif line.strip() in tags:
            tags[line.strip()][0](outputfile, portfolio)
        else:
            outputfile.write(line)
    outputfile.close()    
    
def mainPage(portfolio):

    templateFiles = [ f for f in listdir(TEMPLATE_DIR) if isfile(join(TEMPLATE_DIR, f)) ]

    for template in templateFiles:
        actionTemplate(portfolio, template)
    
    #upload()
    
    #display()
    