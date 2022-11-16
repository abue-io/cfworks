# this script was written by andreas bülhoff in the first half of november 2022 during what felt like the downfall of twitter
# it scrapes the user data of any given account and turns it into pdf files ready to be printed as books, including paratexts and cover designs
# this remediation is a way of archiving ephemeral content due to erratic changes of policies and users deleting their accounts
# it also tries to valorise what was written on the platform as literature worthy to be printed in books
# by this, cfworks seeks to rethink publishing as providing a publishing framework and audience as particulate spheres
# there is no copyright, do with this script whatever you like
# the code notoriously ignores media as well as emojis and most glyphs
# set in the pocketbook format of the print-on-demand platform lulu.com
# sync.ed 2022

import datetime
import json
import os
import time
import pandas as pd
from PIL import Image
import asyncio
from reportlab.lib import utils
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate
import snscrape.modules.twitter as twitterScraper
from tweetcapture import TweetCapture

# insert username without "@" and run the script
username = ""


now = datetime.datetime.now()
year = now.year

# scrapes userdata and saves it to a json file
scraper = twitterScraper.TwitterUserScraper(username, False)
tweets = []
for i,tweet in enumerate(scraper.get_items()):
	tweets.append({"id": tweet.id, "content": tweet.content, "date": tweet.date, "url": tweet.url})
f = open(username + "_tweets.json", "w")
j = json.dumps(tweets, default = str)
f.write(j)
f.close()

# creates a temp json file with data to use for one volume
df_raw = pd.read_json(username + '_tweets.json')
df_inv = df_raw.loc[::-1].reset_index(drop=True)
df_temp = df_inv
df_temp.to_json('temp.json')

volume_number = 1

while df_temp.shape[0] > 0:
    df_temp = pd.read_json('temp.json')
    df = df_temp.head(300)


# cover generation
# get screenshots of first and last tweet printed in volume
    frontcover = df.iloc[0]['url']
    backcover = df.iloc[-1]['url']
    tweet = TweetCapture()
    asyncio.run(tweet.screenshot(frontcover, str(volume_number) + "_front.png", mode=4, night_mode=0))
    asyncio.run(tweet.screenshot(backcover, str(volume_number) + "_back.png", mode=4, night_mode=0))

# cover layout
    coversize=(242 * mm, 181 * mm)
    c=canvas.Canvas(username + "_works_vol_" + str(volume_number) +"_cover.pdf", pagesize=coversize)
    c.translate(mm,mm)
    c.setFont("Helvetica", 14)

# scale and position screenshots on cover
    img = Image.open(str(volume_number) + "_back.png")
    wpercent = (100*mm / float(img.width))
    hsize = int((float(img.height))*float(wpercent))
    c.drawInlineImage(str(volume_number) + "_back.png", 7*mm, 78*mm, width=100*mm, height=hsize)

    img = Image.open(str(volume_number) + "_front.png")
    wpercent = (100*mm / float(img.width))
    hsize = int((float(img.height))*float(wpercent))
    c.drawInlineImage(str(volume_number) + "_front.png",135*mm, 78*mm, width=100*mm, height=hsize)

# draw spine text on cover
    c.rotate(90)
    c.drawString(19*mm, -121*mm, "sync.ed")
    c.drawString(80*mm, -121*mm, "@" + username + "'s Works")
    c.drawString(145*mm, -121*mm, "Vol. " + str(volume_number))

    c.showPage()
    c.save()

    os.remove(str(volume_number) + "_back.png")
    os.remove(str(volume_number) + "_front.png")

# content generation
# format and styles
    pagesize = (114 * mm, 181 * mm)
    c = canvas.Canvas(username + '_works_vol_' + str(volume_number) + '.pdf', pagesize=pagesize)
        
    tweet_style=ParagraphStyle('tweet_style',
    fontName='Helvetica',
    fontSize=14,
    leading=16,
    )

    colo_style=ParagraphStyle('colo_style',
    fontName='Helvetica',
    fontSize=8,
    leading=13,
    )

    number_style=ParagraphStyle('number_style',
    fontName='Helvetica',
    fontSize=10,
    )

# generate title page
    title=Paragraph(
    "@" + username + "'s<br/><br/>Complete Works<font size=10><br/><br/>An Automated Edition of Tweets<br/>In Continuing Volumes<br/><br/>Edited by Andreas Bülhoff</font>", tweet_style)
    title.wrapOn(c, 75 * mm, 58 * mm)
    title.drawOn(c, 19 * mm, 80 * mm)

    editor=Paragraph("sync.ed " + str(year), number_style)
    editor.wrapOn(c, 75 * mm, 58 * mm)
    editor.drawOn(c, 19 * mm, 19 * mm)

    c.showPage()
    c.showPage()

# generate volume title page
    # load dates and change notation to twitter-style
    date1 = df.iloc[0]['date']
    tweetdata_first = datetime.datetime.strptime(str(date1), '%Y-%m-%d %X').strftime('%I:%M %p • %b %d, %Y')
    date2 = df.iloc[-1]['date']
    tweetdata_last = datetime.datetime.strptime(str(date2), '%Y-%m-%d %X').strftime('%I:%M %p • %b %d, %Y')
    
    title=Paragraph("@" + username + "'s<br/><br/>Complete Works<br/><br/>Vol. " + str(volume_number) + "<br/><br/>" + tweetdata_first + "<br/>— " + tweetdata_last, tweet_style)
    title.wrapOn(c, 75 * mm, 58 * mm)
    title.drawOn(c, 19 * mm, 80 * mm)
    
    c.showPage()
    c.showPage()

# generate content pages
    for ind in df.index:
        tweetcontent = df['content'][ind]
        tweetdata_raw  = df['date'][ind]
        tweetdata = datetime.datetime.strptime(str(tweetdata_raw), '%Y-%m-%d %X').strftime('%I:%M %p • %b %d, %Y')
        content=str(tweetcontent)+"<font size=10><br/><br/>"+tweetdata+"</font>"
        tweet=Paragraph(
        content, tweet_style)
        tweet.wrapOn(c, 75 * mm, 58 * mm)
        tweet.drawOn(c, 19 * mm, 90.5 * mm)
        pagenumber=c.getPageNumber()

        if (pagenumber % 2)==0:
            number_style=ParagraphStyle('number_style',
            alignment=TA_LEFT,
            )
        else:
            number_style=ParagraphStyle('number_style',
            alignment=TA_RIGHT,
            )

        number=Paragraph(str(pagenumber), number_style)
        number.wrapOn(c, 75 * mm, 58 * mm)
        number.drawOn(c, 19 * mm, 19 * mm)
        c.showPage()
    
    c.showPage()
    c.showPage()
    
# inserts blank pages if number of tweets in last volume is less than 300
    if df_temp.shape[0] < 300:
        comp=(300-df_temp.shape[0])
        for i in range(comp):
            c.showPage()

# generate colophon
    source_title=Paragraph("Colophon", tweet_style)
    source_title.wrapOn(c, 75 * mm, 58 * mm)
    source_title.drawOn(c, 19 * mm, 165 * mm)

    tweet=Paragraph("This volume is part of an automated and continuous edition of @" + username + "'s works on Twitter. It was made on " + now.strftime("%d/%m/%Y %H:%M:%S") + " using a Python script by Andreas Bülhoff to scrape the complete user data of any given account and transform it into PDF files ready to be printed as books. This process may run counter to the intents of the person who runs the account. However, archiving and caring for the written word should not be left to capitalist platforms.", colo_style)
    tweet.wrapOn(c, 75 * mm, 58 * mm)
    tweet.drawOn(c, 19 * mm, 32 * mm)
    c.showPage()

    number=Paragraph("sync.ed " + str(year), number_style)
    number.wrapOn(c, 75 * mm, 58 * mm)
    number.drawOn(c, 19 * mm, 19 * mm)

    c.showPage()
    c.save()

    volume_number = volume_number + 1
    if df_temp.shape[0] < 300:
        break
    else:
        df_temp = df_temp.drop(df_inv.index[range(300)]).reset_index(drop=True)
        df_temp.to_json('temp.json')

os.remove('temp.json')
print("done")