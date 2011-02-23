#!/usr/bin/env python

import sys, os, errno
from lxml import etree

# create output directory if necessary
try:	
	os.mkdir("static-archive")
except OSError as exc: # Python >2.5
	if exc.errno == errno.EEXIST:
		print "output directory exists"
	else: 
		raise
else:
	print "created output directory"

xslt_doc = etree.parse("statuses2html.xsl")
transform = etree.XSLT(xslt_doc)

doc = etree.parse("master.xml")

result_tree=transform(doc)

# output the master xml
with open ("static-archive/master.html", "w") as f:
	f.write(etree.tostring(result_tree, xml_declaration=True, encoding='utf-8', pretty_print=True))
f.closed



