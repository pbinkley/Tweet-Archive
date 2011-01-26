#!/usr/bin/env python

import sys, time
import oauth2 as oauth

url = sys.argv[1]
filename = sys.argv[2]

print "Fetching " + url + " to " + filename

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

# load secrets	
secrets = getprops("secrets.properties")

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

resp, content = client.request(url, "GET")

print "Response: " + str(resp.status)
if resp.status == 200:
	with open (filename, "w") as f:
		f.write(content)
	f.closed
