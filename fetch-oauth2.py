#!/usr/bin/env python

import sys, os, errno, copy, string
import StringIO
import oauth2 as oauth
from lxml import etree
from copy import deepcopy

# constants
reqcount = 200

def ensure_dir(f):
	d = os.path.dirname(f)
	if not os.path.exists(d):
		os.makedirs(d)


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

def twitter_time_to_str(t):
	# if not a valid twitter timestamp, return empty string
	try:
		return timestamp.strptime(t.replace("+0000 ", ""), '%a %b %d %H:%M:%S %Y').strftime("%Y-%m-%d %H:%M:%S+0000")
	except:
		return ""

timestamp = datetime.now().replace(tzinfo=Local)
tsstr_filename = timestamp.strftime("%Y-%m-%d-%H%M%S")
tsstr_monthpath = timestamp.strftime("%Y/%m")
tsstr = timestamp.strftime("%Y-%m-%d %H:%M:%S%z")

# load secrets	
secrets = getprops("secrets.properties")
# load last_ids
# collect dict containing last id collected from each list
last_ids = getprops("ids.properties")
new_last_ids = copy.deepcopy(last_ids)

# collect ids of referenced tweets
references = []

# collect months represented in this download, in form "2011/02" 
# (for use when creating output file paths)
months = []

# master xml file for output
master = etree.Element("tweetarchive", timestamp_fetch=tsstr)

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
def fetchlist(listpath):
	listname = string.replace(listpath, '/', '_')
	print
	print "Fetching " + listpath
	# start with an empty list
	statuses = etree.Element("statuses", type="array", name=listname)
	page = 1
	finished = False
	id_to = "none"
	id_from = "none"
	timestamp_to = "none"
	timestamp_from = "none"
	
	while finished == False:
		print "Page: " + str(page)
#		url = "http://api.twitter.com/" + listpath + ".xml?include_rts=true&include_entities=true&count=" + str(reqcount) + "&page=" + str(page)
		url = "http://api.twitter.com/" + listpath + ".xml?count=" + str(reqcount) + "&page=" + str(page)
		
#		if id_from != 'none':
#			url += "&max_id=" + str(id_from)

		if listname in last_ids:
			url += "&since_id=" + last_ids[listname]
			print "last id for " + listpath + ": " + last_ids[listname]

		print url
		
		resp, content = client.request(url, "GET")
		
		# resp is of type 'httplib2.Response'
		respdict = dict(resp.items())
		#print "Rate limit remaining: " + respdict['x-ratelimit-remaining'] + " of " + respdict['x-ratelimit-limit']
		#print "    (reset at " + time.strftime("%H:%M:%S %Z, %a, %d %b %Y", time.localtime(float(respdict['x-ratelimit-reset']))) + ")"

		print "Request: " + listpath + " / Response: " + str(resp.status) + " " + resp.reason 
		# parse the XML
		if resp.status == 200:
			contentasfile = StringIO.StringIO(content)
			root = etree.parse(contentasfile)
			
			# determine xpath needed to get individual tweets
			if listname.find('statuses') != -1:
				xp = "/statuses/status"
			elif listname.find('direct_messages') != -1:
				xp = "/direct-messages/direct_message"
			statuscount = int(root.xpath("count(" + xp + ")"))

			if statuscount > 0:
				if page == 1:
					id_to = root.xpath(xp + "[1]/id")[0].text
					timestamp_to = root.xpath(xp + "[1]/created_at")[0].text
					new_last_ids.update({listname: id_to})
				id_from = root.xpath(xp + "[last()]/id")[0].text
				timestamp_from = root.xpath(xp + "[last()]/created_at")[0].text
				
				print "ids:" + str(statuscount) + " from " + id_from + " to " + id_to

				# add newly fetched statuses to our XML
				for status in root.xpath(xp):
					# statusTimestamp format is 2011-02-16 18:48:01+0000
					statusTimestamp = twitter_time_to_str(root.xpath(xp + "[1]/created_at")[0].text)
					statusMonth = statusTimestamp[0:4] + "/" + statusTimestamp[5:7]
					status.set("timestamp", statusTimestamp)
					status.set("month", statusMonth)
					statuses.append(status)
					if status.xpath("in_reply_to_status_id"):
						ref = status.xpath("in_reply_to_status_id")[0].text
						if ref:
							if not ref in references:
								references.append(ref)
#								print "Added " + ref
#							else:
#								print "Dupe " + ref
					if not statusMonth in months:
						months.append(statusMonth)
				page += 1
			else:
				print "reached empty response"
				finished = True
			
			# add to and from attributes to root
			statuses.set("id_to", str(id_to))
			statuses.set("id_from", str(id_from))

			# twitter timestamps are in this format: Sat Oct 16 01:38:40 +0000 2010
			# python can't parse the timezone, so we remove it before parsing
			if timestamp_from != "none":
				td_from_str = twitter_time_to_str(timestamp_from)
			else:
				td_from_str = ""
			if timestamp_to != "none":
				td_to_str = twitter_time_to_str(timestamp_to)
			else:
				td_to_str = ""
			statuses.set("timestamp_from", td_from_str)
			statuses.set("timestamp_to", td_to_str)

			# output the xml
			master.append(statuses)
		else:
			finished=True
			print "Download of " + listpath + " failed."

# now actually do the fetching

fetchlist("statuses/user_timeline")
fetchlist("statuses/mentions")
#fetchlist("statuses/retweets_of_me")
fetchlist("direct_messages")
fetchlist("direct_messages/sent")

# fetch referenced tweets
statuses = etree.Element("statuses", type="array", name="references")
print "Handling " + str(len(references)) + " referenced tweets"

for id in references:
	url = "http://api.twitter.com/statuses/show/" + id + ".xml"
	resp, content = client.request(url, "GET")
	# parse the XML
	
	contentasfile = StringIO.StringIO(content)
	root = etree.parse(contentasfile)

	for status in root.xpath("/status"):
		status.set("timestamp", twitter_time_to_str(root.xpath("created_at")[0].text))
		statuses.append(status)

	# output the xml
	master.append(statuses)

# For each month in current master, create a directory and a download file
# containing the tweets from that month.

for month in months:
	print "    month: " + month
	monthStatuses = etree.Element("tweetarchive", timestamp_fetch=tsstr)
	for statusSet in master.xpath("statuses"):
		setname = statusSet.get("name")
		print "          set: " + setname
		statuses = etree.Element("statuses", type="array")
		statuses.set("name", setname)
		for status in statusSet.xpath("*[@month = '" + month + "']"):
			statuses.append(copy.deepcopy(status))
		monthStatuses.append(statuses)
	filename = "archive/xml/" + month + "/" + tsstr_filename + ".xml"
	ensure_dir(filename)
	with open (filename, "w") as f:
		f.write(etree.tostring(monthStatuses, xml_declaration=True, encoding='utf-8', pretty_print=True))
	f.closed


	
# output the master xml
filename = "archive/masters/" + tsstr_monthpath + "/" + tsstr_filename + ".xml"
ensure_dir(filename)
with open (filename, "w") as f:
	f.write(etree.tostring(master, xml_declaration=True, encoding='utf-8', pretty_print=True))
f.closed


# handle list of last ids
with open ("ids_" + tsstr_filename + ".properties", "w") as f:
	f.write("timestamp = " + tsstr_filename + "\n")
	for key in new_last_ids.keys():
		f.write(key + " = " + new_last_ids.get(key) + "\n")
f.closed

# now rename old file using its timestamp
if 'timestamp' in last_ids:
	lastts = last_ids['timestamp']
else:
	lastts = "first"
try:
	os.rename("ids.properties", "ids_" + lastts + ".properties")
except OSError as exc: # Python >2.5
	# if old ids properties file doesn't exist, that's ok: we'll just create a new one
	if exc.errno == errno.ENOENT:
		pass
	else: 
		raise

# and rename new file to be the default
os.rename("ids_" + tsstr_filename + ".properties", "ids.properties")

