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
# 3. Add the article(s), shipping and/or handling fee.
#

# Here we add a normal product to our goods list.
k.add_article(
	qty=1,  # Quantity
	artno="MG200MMS",  # Article number
	title="Matrox G200 MMS",  # Article name/title
	price=299.99,
	vat=19,  # 19% VAT
	discount=0,
	flags=GoodsIs.INC_VAT)  # Price is including VAT

# Next we might want to add a shipment fee for the delivery
k.add_article(
	qty=1,
	title="Shipping fee",
	price=4.5,
	vat=19,
	discount=0,
	flags=GoodsIs.INC_VAT | GoodsIs.SHIPPING) # Price is including VAT and is a shipment fee

# Lastly, we want to use an invoice/handling fee as well
k.add_article(
	qty=1,
	title="Handling fee",
	price=1.5,
	vat=19,
	discount=0,
	flags=GoodsIs.INC_VAT | GoodsIs.HANDLING) # Price is including VAT and is a handling fee


##
# 3. Create and set the address(es)
#

# Create the address object and specify the values
addr = klarna.Address(
	email='always_accepted@klarna.com',
	telno='',  # We skip the normal land line phone, only one is needed.
	cellno='015 2211 3356',
	fname='Testperson-de',
	lname='Approved',
	careof='',  # No care of, C/O.
	street='Hellersbergstraße',  # For DE and NL specify street number in house_number.
	zip='14601',
	city='Neuss',
	country='DE',
	house_number='14',  # For DE and NL we need to specify houseNo.
	house_extension=None)  # Only required for NL.

# You can also change the properties afterwards
addr.email = 'always_accepted@klarna.com'

# Next we tell the Klarna object to use the address in the next order
k.shipping = addr
k.billing = addr


##
# 4. Specify relevant information from your store (optional)
#

# Set store specific information so you can e.g search and associate invoices
# with order numbers.
k.set_estore_info(
	orderid1='175012',
	orderid2='1999110234',
	user='0005')

# If you don't have the order number available at this stage, you can later
# use the method update_orderno


##
# 5. Set additional information. (optional)
#

## Comment
k.set_comment('A text string stored in the invoice commentary area.')

## Shipment type
k.set_shipment_info(delay_adjust=ShipmentType.EXPRESS)


##
# 6. Invoke activate_reservation and transmit the data
#

# Make sure the order status is ACCEPTED, before activation.
# You can do this by using check_order_status

# Here you enter the reservation number you got from reserve_amount
rno = sys.argv[1]

try:
	# Transmit all the specified data, from the steps above, to Klarna.
	result = k.activate_reservation(
		'07071960',  # Date of birth / pno
		rno,
		Gender.MALE,  # MALE, FEMALE or None if not needed for the active country
		ocr='',  # If you reserved an OCR number earlier
		flags=0,  # No special behaiviour
		pclass=klarna.PClass.Type.INVOICE)  # this is a invoice purchase

	print '%s\t%s' % (result[0], result[1])
except Exception, e:
	logger.debug("call to add_transaction failed", exc_info=True)
	sys.exit(1)
