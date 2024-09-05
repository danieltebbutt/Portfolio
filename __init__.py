import logging
import datetime
import logging
from datetime import date
import os
import io
import urllib.parse as urllib

from azure.storage.blob import BlobServiceClient, ContentSettings

import azure.functions as func

from Portfolio.jsonPublisher import jsonPublisher as publisher
import Portfolio.portfolio as port
from Portfolio.webui import webui
from Portfolio.transaction import transaction

import yfinance as yf

def get_param(req, name, default = None):
    val = req.params.get(name)
    if not val:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            val = req_body.get(name)
    if not val and default != None:
        val = default
    return val

def main(req: func.HttpRequest, portfolioin, pricedata, stocks, portfolioout, pricedataout) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    password = get_param(req, 'password', '')
    if password != os.environ["PASSWORD"]:
         return func.HttpResponse("invalid password")

    command = get_param(req, 'command', '')
    p1 = get_param(req, 'p1')
    p2 = get_param(req, 'p2')
    p3 = get_param(req, 'p3')
    p4 = get_param(req, 'p4')
    p5 = get_param(req, 'p5')
    command = " ".join([x for x in [ command, p1, p2, p3, p4, p5] if x ])

    output = io.StringIO()
    out_stream = io.StringIO()
    portfolio_stream = io.StringIO()
    portfolio_stream.write(portfolioin.read().decode("utf-8"))
    portfolio_stream.seek(0)

    interface = webui(None, None, None, portfolio_stream)
    interface.createHistory(portfolio_stream = portfolio_stream, 
                            price_stream = io.StringIO(pricedata.read().decode("utf-8")),
                            stock_stream = io.StringIO(stocks.read().decode("utf-8")),
                            update_data = (command == "refresh"),
                            price_out_stream = out_stream)
    portfolio_stream.seek(0)

    if command and command != "refresh":
        urllib.unquote_plus(command)
        interface.runCommand(command, output)
    elif command:
        pricedataout.set(out_stream.getvalue())
        output.write("Uploading files\n")
        privateStream = (os.environ["PRIVATE_JSON_BLOB"], io.StringIO())
        publicStream = (os.environ["PUBLIC_JSON_BLOB"], io.StringIO())
        interface.publish(privateStream = privateStream[1], publicStream = publicStream[1])

        connect_str = os.getenv('blobconnection')
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)

        for upload in privateStream, publicStream:
            blob_client = blob_service_client.get_blob_client(container="$web", blob=upload[0])
            upload[1].seek(0)
            blob_client.upload_blob(upload[1].read().encode("utf-8"), overwrite=True, content_settings=ContentSettings(content_type='text/html'))
            output.write("Uploaded %s\n"%upload[0])
        output.write("Uploads done\n")

    portfolio_stream.seek(0)
    portfolioout.set(portfolio_stream.read().encode("utf-8"))

    return func.HttpResponse(output.getvalue())
