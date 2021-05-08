# Web publishing
import os
import configparser
import boto
from boto.s3.key import Key
import posixpath
from os import listdir
from os.path import isfile, join

from .publisher import publisher

class amazonPublisher(publisher):

    OUTPUT_DIR = os.path.normpath("./output")
    DESTINATION = "danieltebbutt.com"
    DETAIL_DIR = "portfolio"

    def upload(self, dir, file):
        config = configparser.ConfigParser()
        config.readfp(open('portfolio.ini'))
        type = config.get("newPublish", "type")
        destination = config.get("newPublish", "destination")

        s3 = boto.connect_s3(is_secure=False)
        bucket = s3.get_bucket(destination, validate=False)

        k = Key(bucket)
        print("Uploading:")

        pathAndFile = join(dir, file)
        fileStream = open(pathAndFile, 'rb')
        k.key = file
        print(file)
        k.set_contents_from_file(fileStream)
        fileStream.close()

    def uploadAll(self, local_dir = OUTPUT_DIR):
        config = configparser.ConfigParser()
        config.readfp(open('portfolio.ini'))
        type = config.get("newPublish", "type")
        destination = config.get("newPublish", "destination")
        
        s3 = boto.connect_s3(is_secure=False)
        bucket = s3.get_bucket(destination, validate=False)
        
        k = Key(bucket)
        print("Uploading:")

        templateFiles = [ f for f in listdir(local_dir) if isfile(join(local_dir,f)) ]
        for file in templateFiles:
            pathAndFile = join(local_dir, file)
            fileStream = open(pathAndFile, 'rb')
            k.key = file
            print(file)
            k.set_contents_from_file(fileStream)
            fileStream.close()

        detailPath = join(local_dir, DETAIL_DIR)
        detailFiles = [ f for f in listdir(detailPath) if isfile(join(detailPath,f)) ]
        for file in detailFiles:
            pathAndFile = join(detailPath, file)
            fileStream = open(pathAndFile, 'rb')
            k.key = posixpath.join(DETAIL_DIR, file)
            print(file)
            k.set_contents_from_file(fileStream)
            fileStream.close()

    def openDetailFile(self, filename):
        directory = os.path.join(self.OUTPUT_DIR, self.DETAIL_DIR)
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        detailFile = open(os.path.join(directory, filename), "w")
        return detailFile

    def closeDetailFile(self, detailFile, filename):
        detailFile.close()

    def mainPage(self):
        templateFiles = [ f for f in listdir(self.TEMPLATE_DIR) if isfile(join(self.TEMPLATE_DIR, f)) ]

        for template in templateFiles:
            outputStream = open(join(self.OUTPUT_DIR,template), 'w')
            self.actionTemplate(template, outputStream)
            outputStream.close()
        self.uploadAll()
        for template in templateFiles:
            self.display(template)
