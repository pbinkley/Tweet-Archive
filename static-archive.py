#!/usr/bin/env python

import sys, os, errno, glob
from lxml import etree

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

def ensure_dir(f):
	d = os.path.dirname(f)
	if not os.path.exists(d):
		os.makedirs(d)

# load secrets (we just need the twitter id)
secrets = getprops("secrets.properties")
twitterID = "'" + secrets['TWITTER_ID'] + "'"

# walk through xml archive directories representing months; generate html for each

# we check whether the transformation needs to be run: are there any dump files
# that are more recent than a pre-existing output file, or is there no output file,
# or is the xsl file more recent than the output file

# prepare the xsl transformer
xsltFile = "statuses2html.xsl"
xslt_doc = etree.parse(xsltFile)
transform = etree.XSLT(xslt_doc)
xsltFileDate = os.path.getmtime(xsltFile)

skipped = 0
transformed = 0

yearDirs= os.listdir("archive/xml")
for yearDir in yearDirs:
	if os.path.isdir("archive/xml/" + yearDir):
		monthDirs = os.listdir("archive/xml/" + yearDir)
		for monthDir in monthDirs:
			if os.path.isdir("archive/xml/" + yearDir + "/" + monthDir):

				outputFile = "archive/html/" + yearDir + "/" + yearDir + "_" + monthDir + ".html"
				# get outputFile modification date (in seconds since epoch)
				try:
					outputFileDate = os.path.getmtime(outputFile)
				except: 
					outputFileDate = 0
				
				# there may be several dump files from multiple fetches
				# so we assemble all the dump files into a single xml tree
				monthTree = etree.Element("month")
				dumpFiles = glob.glob("archive/xml/" + yearDir + "/" + monthDir + "/*.xml")
				
				if outputFileDate == 0 or xsltFileDate > outputFileDate:
					needsTransform = True
				else:
					needsTransform = False
					
				if not needsTransform:
					# check dates of dump files against output file
					for dumpFile in dumpFiles:
						dumpFileDate = os.path.getmtime(dumpFile)
						if dumpFileDate > outputFileDate:
							needsTransform = True
				
				if needsTransform:
					print "Transforming " + yearDir + "/" + monthDir
					transformed += 1
					for dumpFile in dumpFiles:
						doc = etree.parse(dumpFile)
						monthTree.append(doc.getroot())
						timestampFetch = "'" + doc.getroot().get("timestamp_fetch") + "'"

					# run the xsl transformation
					monthName = "'" + yearDir + "-" + monthDir + "'"
					result_tree = transform(monthTree, month=monthName, twitterID=twitterID, timestampFetch = timestampFetch)
		
					# write the html
					print "Saving " + outputFile
					ensure_dir(outputFile)
					# output the master xml
					with open (outputFile, "w") as f:
						f.write(etree.tostring(result_tree, xml_declaration=True, encoding='utf-8', pretty_print=True))
					f.closed
				else:
					print "Skipping " + yearDir + "/" + monthDir
					skipped += 1

print "Finished. Transformed: " + str(transformed) + " months; skipped: " + str(skipped) + " months; total: " + str(transformed + skipped) + " months."




