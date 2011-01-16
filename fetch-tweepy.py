#!/usr/bin/env python

import sys
import tweepy
from lxml import etree

# from http://www.linuxtopia.org/online_books/programming_books/python_programming/python_ch34s04.html
propFile= file( r"secrets.properties", "rU" )
propDict= dict()
for propLine in propFile:
    propDef= propLine.strip()
    if len(propDef) == 0:
        continue
    if propDef[0] in ( '!', '#' ):
        continue
    punctuation= [ propDef.find(c) for c in ':= ' ] + [ len(propDef) ]
    found= min( [ pos for pos in punctuation if pos != -1 ] )
    name= propDef[:found].rstrip()
    value= propDef[found:].lstrip(":= ").rstrip()
    propDict[name]= value
propFile.close()


# all this datetime stuff is from the Python docs:
#     http://docs.python.org/library/datetime.html#tzinfo-objects

# A class capturing the platform's idea of local time.
from datetime import tzinfo, timedelta, datetime

ZERO = timedelta(0)
HOUR = timedelta(hours=1)


import time
# A UTC class.

class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

utc = UTC()

STDOFFSET = timedelta(seconds = -time.timezone)
if time.daylight:
    DSTOFFSET = timedelta(seconds = -time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET

class LocalTimezone(tzinfo):

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, 0)
        stamp = time.mktime(tt)
        tt = time.localtime(stamp)
        return tt.tm_isdst > 0

Local = LocalTimezone()

timestamp = datetime.now().replace(tzinfo=Local)


auth = tweepy.OAuthHandler(propDict['CONSUMER_KEY'], propDict['CONSUMER_SECRET'])
auth.set_access_token(propDict['ACCESS_KEY'], propDict['ACCESS_SECRET'])
api = tweepy.API(auth)
public_tweets = api.home_timeline()

root = etree.Element("tweets")
root.set("timestamp", timestamp.strftime("%Y-%m-%d %H:%M:%S%z"))
root.set("id_to", str(public_tweets[0].id))
root.set("id_from", str(public_tweets[len(public_tweets) - 1].id))
root.set("timestamp_to", public_tweets[0].created_at.replace(tzinfo=utc).astimezone(Local).strftime("%Y-%m-%d %H:%M:%S%z"))
root.set("timestamp_from", public_tweets[len(public_tweets) - 1].created_at.replace(tzinfo=utc).astimezone(Local).strftime("%Y-%m-%d %H:%M:%S%z"))
    
for tweet in public_tweets:
	t = etree.SubElement(root, "tweet")
	t.text = tweet.text
	t.set("id", str(tweet.id))
	t.set("screen_name", tweet.user.screen_name)
	t.set("name", tweet.user.name)
# Twitter dates are UTC, but naive (no tz declared) - so we assign them to utc and then translate to local
	t.set("created_at", tweet.created_at.replace(tzinfo=utc).astimezone(Local).strftime("%Y-%m-%d %H:%M:%S%z"))
	
#print etree.tostring(root)
s = etree.tostring(root, pretty_print=True, encoding='UTF-8', xml_declaration=True)
with open ("output.xml", "w") as f:
	f.write(s)
f.closed

# print the source JSON
# we need to get this: https://github.com/joshthecoder/tweepy/pull/73
#with open('output.json', 'w') as f:
#	json.dump(public_tweets, f, default=to_json)

