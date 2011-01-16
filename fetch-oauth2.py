#!/usr/bin/env python

import sys, os, errno
import StringIO
import oauth2 as oauth
from lxml import etree

# constants
reqcount = 100

# load properties from files
# from http://www.linuxtopia.org/online_books/programming_books/python_programming/python_ch34s04.html
def getprops(filename):
	#propFile= file( r"secrets.properties", "rU" )
	propDict= dict()
	try:
		with open (filename, "rU") as propFile:
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
	except (IOError):
		print filename + ".properties not found"
	return propDict

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
tsstr_filename = timestamp.strftime("%Y-%m-%d-%H%M%S")
tsstr = timestamp.strftime("%Y-%m-%d %H:%M:%S%z")

# load secrets	
secrets = getprops("secrets.properties")
# load last_ids
# collect dict containing last id collected from each list
last_ids = getprops("ids.properties")

# Set up your Consumer and Token and Client
consumer = oauth.Consumer(secrets['CONSUMER_KEY'], secrets['CONSUMER_SECRET'])
token = oauth.Token(secrets['ACCESS_KEY'], secrets['ACCESS_SECRET'])
client = oauth.Client(consumer, token)

### Make the auth request ###

# Set the API endpoint 
endpoint = "https://api.twitter.com/oauth/request_token"

# Set the base oauth_* parameters along with any other parameters required
# for the API call.
oauth_params = {
    'oauth_version': "1.0",
    'oauth_nonce': oauth.generate_nonce(),
    'oauth_timestamp': int(time.time()),
	'oauth_token': secrets['ACCESS_KEY'],
	'oauth_consumer_key': secrets['CONSUMER_KEY']
}

# Create our request. 
req = oauth.Request(method="POST", url=endpoint, parameters=oauth_params)

# Sign the request.
signature_method = oauth.SignatureMethod_HMAC_SHA1()
req.sign_request(signature_method, consumer, token)

# function to fetch a given list, iterating through pages until all the tweets have
# been received
def fetchlist(listname):
	print
	print "Fetching " + listname
	# start with an empty list
	statuses = etree.Element("statuses", type="array")
	page = 1
	finished = False
	id_to = "none"
	id_from = "none"
	timestamp_to = "none"
	timestamp_from = "none"
	
	while finished == False:
		print "Page: " + str(page)
	#	url = "http://api.twitter.com/statuses/" + listname + ".xml?since_id=16557754105729024&page=" + str(page)
		url = "http://api.twitter.com/statuses/" + listname + ".xml?count=" + str(reqcount) + "&page=" + str(page)

		if listname in last_ids:
			url += "&since_id=" + last_ids[listname]
			print "last id for " + listname + ": " + last_ids[listname]

		print url
		
		resp, content = client.request(url, "GET")

		# resp is of type 'httplib2.Response'

		print "Request: " + listname + " / Response: " + str(resp.status) + " " + resp.reason 
		# parse the XML
	
		contentasfile = StringIO.StringIO(content)
		root = etree.parse(contentasfile)

		statuscount = int(root.xpath("count(/statuses/status)"))
		if statuscount > 0:
			if page == 1:
				id_to = root.xpath("/statuses/status[1]/id")[0].text
				timestamp_to = root.xpath("/statuses/status[1]/created_at")[0].text
				last_ids.update({listname: id_to})
			id_from = root.xpath("/statuses/status[last()]/id")[0].text
			timestamp_from = root.xpath("/statuses/status[last()]/created_at")[0].text
			
			print "ids:" + str(statuscount) + " from " + id_from + " to " + id_to
			for status in root.xpath("/statuses/status"):
				statuses.append(status)
			page += 1
		else:
			print "empty response"
			finished = True
		if statuscount < reqcount:
			print "last response"
			finished = True
			
	# add fetch, to and from attributes to root
	statuses.set("timestamp_fetch", tsstr)
	statuses.set("id_to", str(id_to))
	statuses.set("id_from", str(id_from))

	# twitter timestamps are in this format: Sat Oct 16 01:38:40 +0000 2010
	# python can't parse the timezone, so we remove it before parsing
	if timestamp_from != "none":
		td_from_str = timestamp.strptime(timestamp_from.replace("+0000 ", ""), '%a %b %d %H:%M:%S %Y').strftime("%Y-%m-%d %H:%M:%S+0000")
	else:
		td_from_str = ""
	if timestamp_to != "none":
		td_to_str = timestamp.strptime(timestamp_to.replace("+0000 ", ""), '%a %b %d %H:%M:%S %Y').strftime("%Y-%m-%d %H:%M:%S+0000")
	else:
		td_to_str = ""
	statuses.set("timestamp_from", td_from_str)
	statuses.set("timestamp_to", td_to_str)
			


	# output the xml
	with open ("output/" + listname + "_" + tsstr_filename + ".xml", "w") as f:
		f.write(etree.tostring(statuses, xml_declaration=True, encoding='utf-8', pretty_print=True))
	f.closed

# create output directory if necessary
try:	
	os.mkdir("output")
except OSError as exc: # Python >2.5
	if exc.errno == errno.EEXIST:
		print "output directory exists"
	else: 
		raise
else:
	print "created output directory"


# now actually do the fetching

fetchlist("user_timeline")
fetchlist("mentions")
fetchlist("retweets_of_me")

# handle list of last ids
with open ("ids_" + tsstr_filename + ".properties", "w") as f:
	f.write("timestamp = " + tsstr_filename + "\n")
	for key in last_ids.keys():
		f.write(key + " = " + last_ids.get(key) + "\n")
f.closed

# now rename old file using its timestamp
os.rename("ids.properties", "ids_" + last_ids['timestamp'] + ".properties")

# and rename new file to be the default
os.rename("ids_" + tsstr_filename + ".properties", "ids.properties")