#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import klarna
from klarna.const import *


##
# 0. Enable debug info (optional)
#
# See http://docs.python.org/library/logging.html for more options of the
# logging framework in python

import logging
logger = logging.getLogger('klarna')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


##
# 1A. Set configuration programatically (Alternative 1)
#

# You can specify any number of configuration options at creation
config = klarna.Config(
	eid=0,  # Merchant ID or Estore ID, an integer above 0
	secret='sharedSecret',  # The shared secret which accompanied your eid
	country='DE',
	language='DE',
	currency='EUR',
	mode='beta')  # 'live' or 'beta', depending on which server your eid is associated with

# Or set them later as Config implements the mapping protocol
config['pcstorage'] = 'json'  # Which storage module to use for PClasses. currently only 'json' available
config['pcuri'] = '/srv/pclasses.json'  # Where the json file for the pclasses are stored

# Should http or https be used when communicating with Klarna, defaults to https
config['scheme'] = 'https'

# Should we error report/status report to Klarna
config['candice'] = True  # set to False if your server doesn't support UDP

# Enable xml-rpc debug
config['dumpxml'] = False


##
# 1B: Use any object implementing the mapping protocol (Alternative 2)
#

import collections
config = collections.OrderedDict()


##
# 1C: Load configuration from json (Alternative 3)
#

# Load configuration from /srv/klarna.json, make sure this file is not
# readable by unauthorized person as it will contain sensitve data
config = klarna.Config('/srv/klarna.json')

# The file would contain the following data if following the steps above
'''{
	"eid": 0,
	"secret": "sharedSecret",
	"country": "DE",
	"language': DE",
	"currency": "EUR",
	"mode": "beta",
	"pcstorage": "json,
	"pcuri: "/srv/pclasses.json",
	"scheme": "https",
	"candice": true,
	"dumpxml": false
}'''


##
# 2. Initialise and setup the Klarna instance
#

k = klarna.Klarna(config)
k.init()


## Set customer IP
# Klarna can parse a WSGI environment to get this information
#k.parse_wsgi_env(env)

# or you can specify the address directly
k.clientip = '83.10.0.5'


##
# 3. Get the adress(es) from Klarna. (Sweden only!)
#
k.country = 'SE'
k.currency = 'SEK'
k.language = 'DE'

try:
	# Attempt to get the adress(es) associated with the SSN/PNO
	addrs = k.get_addresses('410321-9202')

	# if there exist several addresses you would want to output a list in which
	# the customer could choose the address.

	for i,addr in enumerate(addrs):
		if addr.is_company:
			print "Company name:", addr.company
		else:
			print "First name:", addr.fname
			print "Last name:", addr.lname
		print "Street:", addr.street
		print "Zip code:", addr.zip
		print "City:", addr.city
		print "Country", addr.country

		if i != len(addrs) - 1:
			print "\n"

except Exception, e:
	logger.debug("call to add_transaction failed", exc_info=True)
	sys.exit(1)
