#!/usr/bin/env python

import sys

import oauth2 as oauth

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

# Set up your Consumer and Token as per usual. Just like any other
# three-legged OAuth request.
consumer = oauth.Consumer(propDict['CONSUMER_KEY'], propDict['CONSUMER_SECRET'])
token = oauth.Token(propDict['ACCESS_KEY'], propDict['ACCESS_SECRET'])

client = oauth.Client(consumer, token)


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
tsstr = timestamp.strftime("%Y-%m-%d-%H%M%S")

# Set the API endpoint 
endpoint = "https://api.twitter.com/oauth/request_token"

# Set the base oauth_* parameters along with any other parameters required
# for the API call.
params = {
    'oauth_version': "1.0",
    'oauth_nonce': oauth.generate_nonce(),
    'oauth_timestamp': int(time.time())
}


# Set our token/key parameters
params['oauth_token'] = propDict['ACCESS_KEY']
params['oauth_consumer_key'] = propDict['CONSUMER_KEY']

# Create our request. Change method, etc. accordingly.
req = oauth.Request(method="POST", url=endpoint, parameters=params)

# Sign the request.
signature_method = oauth.SignatureMethod_HMAC_SHA1()
req.sign_request(signature_method, consumer, token)

### Make the auth request ###
def getlist(listname):
	url = "http://api.twitter.com/statuses/" + listname + ".xml"

	resp, content = client.request(url, "GET")

	# resp is of type 'httplib2.Response'

	print url
	print content # prints 'ok'

	with open ("output/" + listname + "_" + tsstr + ".xml", "w") as f:
		f.write(content)
	f.closed
	
getlist("user_timeline")
getlist("mentions")
