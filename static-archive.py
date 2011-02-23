#!/usr/bin/env python

import sys, os, errno
from lxml import etree

# create output directory if necessary
try:	
	os.mkdir("static-archive")
except OSError as exc: # Python >2.5
	if exc.errno == errno.EEXIST:
		print "static-archive directory exists"
	else: 
		raise
else:
	print "created static-archive directory"

xslt_doc = etree.parse("statuses2html.xsl")
transform = etree.XSLT(xslt_doc)

dirList= sorted(os.listdir("output"), reverse=True)
 
doc = etree.parse("output/" + dirList[0] + "/master.xml")

result_tree=transform(doc)

# create directory
try:
	os.mkdir("static-archive/" + dirList[0])
except OSError as exc: # Python >2.5
	if exc.errno == errno.EEXIST:
		print "static-archive timestamp directory exists"
	else: 
		raise
else:
	print "created static-archive timestamp directory"


# output the master xml
with open ("static-archive/" + dirList[0] + "/master.html", "w") as f:
	f.write(etree.tostring(result_tree, xml_declaration=True, encoding='utf-8', pretty_print=True))
f.closed



