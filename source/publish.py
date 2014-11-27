# Web publishing

import operator
import ftplib
import webbrowser
import math


filename = "portfolio.html"
path = "\\danieltebbutt.com\\"
destination = "danieltebbutt.com"

dollar_sign=u'\N{dollar sign}'
pound_sign=u'\N{pound sign}'


def publish(portfolio, outputfile):

    today = portfolio.history[portfolio.today()]
    total = 0
    shares = []
    for index, share in today.shares.iteritems():
        shares.append((share.stock,today.share_invested(share.stock),share.avg_purchase_price,share.price,share.accumulated_earnings / (share.number + share.number_sold),share.profit(),share.avg_raw_invested(),share.holding_period()))
    shares.sort(key=operator.itemgetter(1))
    shares.reverse()
    total_invested = today.total_invested() - portfolio.sector_invested("Currency", today)

    outputfile.write("\
<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">\
<HTML>\
<HEAD>\
<META HTTP-EQUIV=\"CONTENT-TYPE\" CONTENT=\"text/html; charset=windows-1252\">\
<TITLE>Dan's share portfolio</TITLE>\
<META NAME=\"GENERATOR\" CONTENT=\"stocktrack.py\">\
<META NAME=\"AUTHOR\" CONTENT=\"Daniel Tebbutt\">\
<META NAME=\"CREATED\" CONTENT=\"20100127;19135800\">\
<META NAME=\"CHANGEDBY\" CONTENT=\"Daniel Tebbutt\">\
<META NAME=\"CHANGED\" CONTENT=\"20100127;19185500\">\
<STYLE TYPE=\"text/css\">\
<!--\
    @page { margin: 2cm }\
    P { margin-bottom: 0.21cm }\
    TD P { margin-bottom: 0cm }\
-->\
</STYLE>\
<script src=\"sorttable.js\"></script>\
</HEAD>\
<BODY LANG=\"en-GB\" DIR=\"LTR\">\
<STYLE>\
.dantable, .dantable TD, .dantable TH\
{\
font-size:10pt;\
}\
</STYLE>\
<TABLE WIDTH=100%% BORDER=0>\
<TR>\
<TD valign=\"top\" width=25%%>\
<DIV ALIGN=\"Left\">Last updated: %2d/%2d/%4d</DIV>\
</TD>\
<TD width=50%%>\
<DIV ALIGN=\"Center\">\
<CENTER>\
<H1>\
Dan's share portfolio\
</H1>\
</CENTER>\
</DIV>\
</TD>\
<TD VALIGN=\"top\" WIDTH=25%%>\
<DIV ALIGN=\"Right\">\
<A HREF=\"index.html\">Back to main menu</A>\
</DIV>\
</TD>\
</TR>\
</TABLE>\
<TABLE WIDTH=100%% CELLSPACING=2><TD VALIGN=\"top\">"%(portfolio.today().day,portfolio.today().month,portfolio.today().year))

    counter=0
    datastring="0"
    sizestring="0"
    rawstring="0"
    monthstring="|Jan|"
    yearstring="|2008"
    months={}
    months[1] = "Jan"
    months[2] = ""
    months[3] = ""
    months[4] = "Apr"
    months[5] = ""
    months[6] = ""
    months[7] = "Jul"
    months[8] = ""
    months[9] = ""
    months[10] = "Oct"
    months[11] = ""
    months[12] = ""
    minvalue=0
    maxvalue=0

    max_invested = 0
    peak_size = 0
    for date in sorted(portfolio.history):
        day = portfolio.history[date]
        if day.raw_share_invested() > max_invested:
            max_invested = day.raw_share_invested()
        if day.total_share_invested() > peak_size:
            peak_size = day.total_share_invested()

    print "Maximum invested = %s%.2f"%(pound_sign, max_invested/100)
    print "Peak size = %s%.2f"%(pound_sign, peak_size/100)

    for date in sorted(portfolio.history):
        day = portfolio.history[date]
        if day.date.day == 1:
            monthstring="%s%s|"%(monthstring, months[day.date.month])
            if day.date.month == 1:
                yearstring="%s|%s"%(yearstring, day.date.year)
            else:
                yearstring="%s|"%yearstring
        counter=counter+1
        if counter == 28:
            counter = 0
            value=(day.profit() - day.currency_profit())*100/max_invested
            datastring="%s,%.2f"%(datastring,value)
            sizestring="%s,%.2f"%(sizestring,((100 * day.total_share_invested()) / peak_size))
            rawstring="%s,%.2f"%(rawstring,((100 * day.raw_share_invested()) / peak_size))
            if value > maxvalue:
                maxvalue = value
            if value < minvalue:
                minvalue = value
    if counter != 0:
        value=(day.profit() - day.currency_profit())*100/max_invested
        datastring="%s,%.2f"%(datastring,value)
        sizestring="%s,%.2f"%(sizestring,((100 * day.total_share_invested()) / peak_size))
        rawstring="%s,%.2f"%(rawstring,((100 * day.raw_share_invested()) / peak_size))
        if value > maxvalue:
            maxvalue = value
        if value < minvalue:
            minvalue = value

    maxvalue = math.ceil(maxvalue / 10) * 10
    minvalue = math.floor(minvalue / 10) * 10

    y_axis="|"
    for value in range(int(minvalue),int(maxvalue)+10,10):
        y_axis="%s%s|"%(y_axis, value)

    sector_info=[]
    for sector in portfolio.sectors:
        if sector != "Currency" and portfolio.sector_invested(sector, today) > 0:
            sector_info.append((sector,(portfolio.sector_invested(sector, today)*100)/today.total_share_invested()))

    sector_info.sort(key=operator.itemgetter(1))
    sector_info.reverse()

    sector_size_string=""
    sector_label_string=""
    for sector_item in sector_info:
        if sector_size_string == "":
            sector_size_string="%s"%sector_item[1]
            sector_label_string="%s"%sector_item[0]
        else:
            sector_size_string="%s,%s"%(sector_size_string, sector_item[1])
            sector_label_string="%s|%s"%(sector_label_string, sector_item[0])

    asset_info=[]
    for desc in portfolio.descriptions:
        if desc != "Currency" and portfolio.description_invested(desc, today) > 0.1:
            asset_info.append((desc,(portfolio.description_invested(desc, today)*100)/today.total_share_invested()))

    asset_info.sort(key=operator.itemgetter(1))
    asset_info.reverse()

    asset_size_string=""
    asset_label_string=""
    for asset_item in asset_info:
        if asset_size_string == "":
            asset_size_string="%s"%asset_item[1]
            asset_label_string="%s"%asset_item[0].replace(" ","+")
        else:
            asset_size_string="%s,%s"%(asset_size_string, asset_item[1])
            asset_label_string="%s|%s"%(asset_label_string, asset_item[0].replace(" ","+"))

    outputfile.write("<DIV ALIGN=\"Left\">\
<B>Current portfolio (%d%% of peak size)</B><BR>\
</DIV>\
<TABLE WIDTH=100%% BORDER=1 BORDERCOLOR=\"#888888\" CELLPADDING=2 CELLSPACING=0 CLASS=\"sortable\" style=\"font-size:12px\">\
<TR VALIGN=TOP>\
    <TH>\
        Share\
    </TH>\
    <TH>\
        Ticker\
    </TH>\
    <TH TITLE=\"Percentage of portfolio value\">\
        Percentage\
    </TH>\
    <TH TITLE=\"Average purchase price\">\
        Bought at (p)\
    </TH>\
    <TH TITLE=\"Current price\">\
        Current (p)\
    </TH>\
    <TH TITLE=\"Average per-share accumulated dividends received\">\
        Dividends (p)\
    </TH>\
    <TH TITLE=\"Average per-share profit, including capital gain and dividends received\">\
        Profit\
    </TH>\
    <TH TITLE=\"Average annual per-share profit, including capital gain and dividends received\">\
        Annual profit\
    </TH>\
</TR>"%((100 * today.total_share_invested()) / peak_size))

    for stock in shares:
        if portfolio.investments[stock[0]].sector != "Currency":
            outputfile.write("  <TR VALIGN=TOP>\
    <TD>\
        %s\
    </TD>\
    <TD>\
        %s\
    </TD>\
    <TD>\
        %.1f%%\
    </TD>\
    <TD>\
        %.1f\
    </TD>\
    <TD>\
        %.1f\
    </TD>\
    <TD>\
        %.1f\
    </TD>\
    <TD>\
        <FONT COLOR=\"%s\">%.1f%%</FONT>\
    </TD>\
    <TD>\
        <FONT COLOR=\"%s\">%.1f%%</FONT>\
    </TD>\
</TR>"%(portfolio.investments[stock[0]].fullname,stock[0],\
        (stock[1]*100)/total_invested,stock[2],stock[3],stock[4],\
        ("#008000" if ((stock[3] + stock[4] - stock[2]) >= 0) else "#800000"),\
        (100*(stock[3] + stock[4] - stock[2]))/stock[2],\
        ("#008000" if ((stock[3] + stock[4] - stock[2]) >= 0) else "#800000"),\
        100*(((1+(stock[5]/stock[6]))**(365.0/stock[7]))-1)))

    outputfile.write("</TABLE>")

    outputfile.write("\
<B>Former holdings</B><BR>\
<TABLE WIDTH=100%% BORDER=1 BORDERCOLOR=\"#888888\" CELLPADDING=2 CELLSPACING=0 CLASS=\"sortable\" style=\"font-size:12px\">\
<TR VALIGN=TOP>\
    <TH>\
        Share\
    </TH>\
    <TH>\
        Ticker\
    </TH>\
    <TH TITLE=\"Average purchase price\">\
        Bought at (p)\
    </TH>\
    <TH TITLE=\"Average sale price\">\
        Sold at (p)\
    </TH>\
    <TH TITLE=\"Average per-share accumulated dividends received\">\
        Dividends (p)\
    </TH>\
    <TH TITLE=\"Average per-share profit, including capital gain and dividends received\">\
        Profit\
    </TH>\
    <TH TITLE=\"Average annual per-share profit, including capital gain and dividends received\">\
        Annual profit\
    </TH>\
</TR>")
    sold_shares=[]
    for index, sharelist in today.sold_shares.iteritems():
        num = 0
        for share in sharelist:
            num = num + 1
        ii = 0
        for share in sharelist:
            ii = ii + 1
            profit = 100*(share.avg_sale_price + (share.accumulated_earnings / share.number_sold) - share.avg_purchase_price) / share.avg_purchase_price
            annual_profit = 100*(((1+(share.profit()/share.avg_raw_invested()))**(365.0/share.holding_period()))-1)
            share.running_profit(),share.avg_raw_invested(),share.holding_period()
            if num == 1:
                name = portfolio.investments[share.stock].fullname
            else:
                name = "%s (%d)"%(portfolio.investments[share.stock].fullname, ii)
            sold_shares.append((name,share.stock,share.avg_purchase_price,share.avg_sale_price,share.accumulated_earnings / share.number_sold, ("#008000" if (profit >= 0) else "#800000"),profit, ("#008000" if (profit >= 0) else "#800000"),annual_profit))
    sold_shares.sort(key=operator.itemgetter(6))
    sold_shares.reverse()

    for share in sold_shares:
        if portfolio.investments[share[1]].sector != "Currency":
            outputfile.write("  <TR VALIGN=TOP>\
    <TD>\
        %s\
    </TD>\
    <TD>\
        %s\
    </TD>\
    <TD>\
        %.1f\
    </TD>\
    <TD>\
        %.1f\
    </TD>\
    <TD>\
        %.1f\
    </TD>\
    <TD>\
        <FONT COLOR=\"%s\">%.1f%%</FONT>\
    </TD>\
    <TD>\
        <FONT COLOR=\"%s\">%.1f%%</FONT>\
    </TD>\
</TR>"%share)

    outputfile.write("</TABLE>")

    outputfile.write("<DIV style=\"font-size=12px\">Note: purchase and sale prices are averaged across all trades for the share in question.<BR>\
    To sort on a particular heading just click on it.</DIV>")

    outputfile.write("</TD><TD valign=\"top\">")

    outputfile.write("\
<IMG SRC=http://chart.apis.google.com/chart?cht=lc&chs=450x250&chxt=x,y,x&chxl=0:%s1:%s2:%s&chd=t:%s&chds=%d,%d&chg=0,%.3f,0&chtt=Profit title=\"Profit over time as a percentage of maximum sum invested\" alt=\"Profit\"></IMG><BR>"%\
    (monthstring, y_axis, yearstring, datastring, minvalue, maxvalue, 1000/(maxvalue-minvalue)))

    outputfile.write("\
<IMG SRC=http://chart.apis.google.com/chart?cht=lc&chs=450x250&chxt=x,y,x&chco=FF0000,0000FF&chg=0,20,0&chxl=0:%s2:%s&chd=t:%s&chds=%d,%d&chtt=Size title=\"Size over time as a percentage of peak\" alt=\"Size\"></IMG><BR>"%\
    (monthstring, yearstring, sizestring, 0, 100))

    outputfile.write("\
<IMG SRC=http://chart.apis.google.com/chart?cht=lc&chs=450x250&chxt=x,y,x&chco=FF0000,0000FF&chxl=0:%s1:%s2:%s&chg=0,33.333,0&chd=t:%s|%s&chds=%d,%d&chtt=Size+vs+net+invested title=\"Size vs net sum invested as percentage of peak size\" alt=\"Value\"></IMG><BR>"%\
    (monthstring, "|-50|-25|0|25|50|75|100|", yearstring, sizestring, rawstring, -50, 100))

    outputfile.write("\
<BR><BR>\
<IMG SRC=http://chart.apis.google.com/chart?cht=p3&chd=t:%s&chs=450x200&chl=%s&chco=FF0000,0000FF,00FF00,FFFF00,00FFFF,FF00FF&chtt=Sector title=\"Percentage of portfolio invested in each sector\" alt=\"Sector\"></IMG><BR>"%\
    (sector_size_string, sector_label_string))

    outputfile.write("\
<BR><BR>\
<IMG SRC=http://chart.apis.google.com/chart?cht=p3&chd=t:%s&chs=450x200&chl=%s&chco=FF0000,0000FF,00FF00,FFFF00,00FFFF,FF00FF&chtt=Asset+class title=\"Percentage of portfolio invested in each asset class.  Preference shares classified as bonds.\" alt=\"Asset class\"></IMG><BR>"%\
    (asset_size_string, asset_label_string))

    outputfile.write("</TD></TABLE>\
<!-- Start of StatCounter Code -->\
<script type=\"text/javascript\">\
var sc_project=5539639; \
var sc_invisible=1; \
var sc_partition=60; \
var sc_click_stat=1; \
var sc_security=\"4f96bb2e\"; \
</script>\
\
<script type=\"text/javascript\"\
src=\"http://www.statcounter.com/counter/counter.js\"></script><noscript><div\
class=\"statcounter\"><a title=\"stats for wordpress\"\
href=\"http://www.statcounter.com/wordpress.org/\"\
target=\"_blank\"><img class=\"statcounter\"\
src=\"http://c.statcounter.com/5539639/0/4f96bb2e/1/\"\
alt=\"stats for wordpress\" ></a></div></noscript>\
<!-- End of StatCounter Code -->\
</BODY>\
</HTML>")
    
def upload():    
    outputfile = open("%s\\%s"%(path,filename), 'rb')

    session = ftplib.FTP("ftp.%s"%destination)
    password = raw_input("Password?")
    session.login(destination, password)
    session.storbinary("STOR wwwroot\\%s"%filename, outputfile)
    outputfile.close()
    session.quit()
    
def display():
    webbrowser.open("http://www.%s/%s"%(destination,filename))

def main_page(portfolio):
    outputfile = open("%s\\%s"%(path,filename), "wb")
    
    # Write to web page
    publish(portfolio, outputfile)
    
    outputfile.close()
    
    upload()
    
    display()
    