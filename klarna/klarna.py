#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' Klarna API

Defines the main API object class used to communicate with Klarna
'''

# Copyright 2011 KLARNA AB. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY KLARNA AB "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL KLARNA AB OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of KLARNA AB.

# python3k campatibility
from __future__ import print_function
import sys
if sys.version_info >= (3,):
	import xmlrpc.client as xmlrpc
	from html.entities import name2codepoint
	basestring = str
else:
	import htmlentitydefs
	import xmlrpclib as xmlrpc

__all__ = ('Klarna',)

# System imports
import logging
import re
import time
from functools import partial

# Klarna submodules
from .const import *
from .error import *
from .addr import Address
from .pclass import PClass
from .candice import Candice
from .digest import get_digest
from . import pclasses, checkout

# logger shortcut
logger = logging.getLogger('klarna')


class ServerProxy(xmlrpc.ServerProxy):
	''' Wrapper around xmlrpc ServerProxy that enables logging and statistics
		gathering of all calls.
	'''

	candice = None

	def __getattr__(self, key):
		method = xmlrpc.ServerProxy.__getattr__(self, key)

		def callwrapper(*args):
			status = 0
			start = time.time()
			logger.debug("calling %s(%s)",
				key, ', '.join([str(x) for x in args]))

			try:
				result = method(*args)

			except xmlrpc.Fault as e:
				# Grab the fault code in case it's going to be sent to candice
				status = e.faultCode
				raise e

			finally:
				end = time.time()
				# Send xml-rpc call stats to candice if requested
				if self.candice is not None:
					duration = int(end - start)
					self.candice.send_stat(key, duration, duration, status)

			logger.debug("[result] %s : %s", key, result)
			return result
		return callwrapper


def check_type(field, v, types, tag=None):
	''' Raises TypeError unless v is a instance of any of the provided types '''

	if not isinstance(v, types):
		raise TypeError("%s not an %s (%s %r)" %
			(field, ' or '.join([t.__name__ for t in types]), type(v), v))

	if tag is not None:
		if isinstance(v, Tag) and not isinstance(v, tag):
			raise TypeError("Tagged value %r not of expected type %s (was %s)" %
				(v, tag, type(v)))

	return v


def remote_call(fun):
	''' Decorates the function fun with a check for the xmlrpc object '''
	def remote_call_wrapper(klarna, *args, **kwargs):
		if not hasattr(klarna, 'xmlrpc'):
			raise MissingXmlRpc()
		return fun(klarna, *args, **kwargs)
	remote_call_wrapper.__doc__ = fun.__doc__
	return remote_call_wrapper


def fix_amount(amount):
	return int(round(amount * 100))


class Tag(str):
	''' Used as base class for str subclasses used by Klarna API '''
	def __new__(cls, tostr, klarna=None):
		o = str.__new__(cls, tostr)
		o.klarna = klarna
		return o


def buildversion(v):
	# split package version into dotted version and extension
	vparts = v.split('-', 1)
	# build a version string like language:type:version:extra
	return ':'.join(['python', 'api'] + vparts)


class Klarna(object):
	'''
		This API provides a way to integrate with Klarna's services over the
		XML-RPC protocol.

		For more information see http://integration.klarna.com/en/api/step-by-step
	'''

	PROTO = '4.1'
	VERSION = buildversion(version)

	## Types used to tag arguments/return values with their use
	class OCR(Tag):
		''' OCR Number '''
		pass

	class INVNO(Tag):
		''' Invoice Number '''
		def amount(self):  # pragma: no cover
			return self.klarna.invoice_amount(self)

	class CUSTNO(Tag):
		''' Customer Number '''
		pass

	class PNO(Tag):
		''' Personal Number / Social security number '''
		pass

	class RNO(Tag):
		''' Reservation number '''
		pass

	# The protocol to use when communicating with Klarna (http or https)
	scheme = 'https'

	# Iff the estore is using a proxy which populates the clients IP to
	# x_forwarded_for then this should be set to True
	use_x_forwarded_for = False

	# URL of the candice server
	c_addr = 'clientstat.kreditor.se'

	# Port number to use for candice
	c_port = 80

	# Server definitions (url, default configuration)
	servers = {
		'live': ('payment.klarna.com', {'scheme': 'https'}),
		'beta': ('payment-beta.klarna.com', {'scheme': 'https'})}

	# default ports to use for http/https (standard RFC ports)
	default_ports = {
		'http': 80,
		'https': 443}

	# Default values for instances
	_client_addr = None
	_xfwd_addr = None
	pclasses = None
	co_objects = None

	@property
	def eid(self):
		''' The estore's identifier received from Klarna '''
		if hasattr(self, '_eid'):
			return self._eid
		return self.config['eid']

	@eid.setter
	def eid(self, value):
		self._eid = int(value)

	@property
	def secret(self):
		''' The estore's shared secret with klarna '''
		if hasattr(self, '_secret'):
			return self._secret
		return self.config['secret']

	@secret.setter
	def secret(self, value):
		self._secret = str(value)

	@property
	def country(self):
		''' Country code
			code must be one of the keys in the Countries dictionary '''
		if hasattr(self, '_country'):
			return self._country
		return self.config['country']

	@country.setter
	def country(self, value):
		try:
			self._country = lookup(Countries, value)
		except ValueError:
			raise UnknownCountry(value)

	@property
	def language(self):
		''' Language code
			code must be one of the keys in the Languages dictionary '''
		if hasattr(self, '_language'):
			return self._language
		return self.config['language']

	@language.setter
	def language(self, value):
		if value not in Languages:
			raise UnknownCountry(value)
		self._language = value

	@property
	def currency(self):
		''' Currency code
			code must be one of the keys in the Currencies dictionary '''
		if hasattr(self, '_currency'):
			return self._currency
		return self.config['currency']

	@currency.setter
	def currency(self, value):
		if value not in Currencies:
			raise KlarnaException("Unknown currency '%s'" % value)
		self._currency = value

	@property
	def billing(self):
		''' Billing address used in the transaction
			shipping address will be used if not set '''
		if hasattr(self, '_billing'):
			return self._billing
		if not hasattr(self, '_shipping'):
			raise AttributeError("No Address set")
		return self._shipping

	@billing.setter
	def billing(self, value):
		logger.debug("Billing address %s", value)
		self._billing = value

	@property
	def shipping(self):
		''' Shipping address used in the transaction
			billing address will be used if not set '''
		if hasattr(self, '_shipping'):
			return self._shipping
		if not hasattr(self, '_billing'):
			raise AttributeError("No Address set")
		return self._billing

	@shipping.setter
	def shipping(self, value):
		logger.debug("Shipping address %s", value)
		self._shipping = value

	@property
	def comment(self):
		''' Comment string used in the transaction, the comment will be shown
			in the invoice.
		'''
		return '\n'.join(self._comments)

	@property
	def extrainfo(self):
		''' Extra info used in the transaction

			Available named values are:
			* str - cust_no
			* str - estore_user
			* str - maiden_name
			* str - place_of_birth
			* str - password
			* str - new_password
			* str - captcha
			* int - poa_group
			* str - poa_pno
			* str - ready_date
			* str - rand_string
			* int - bclass
			* str - pin
		'''
		return self._extrainfo

	@property
	def bankinfo(self):
		''' Bank info used in the transaction

			Available named values are:
			* int - bank_acc_bic
			* int - bank_acc_no
			* int - bank_acc_pin
			* int - bank_acc_tan
			* str - bank_name
			* str - bank_city
			* str - iban
		'''
		return self._bankinfo

	@property
	def incomeinfo(self):
		''' Income info used in the transaction

			Available named values are:
			* int - yearly_salary
			* int - no_people_in_household
			* int - no_children_below_18
			* int - net_monthly_household_income
			* int - monthly_cost_accommodation
			* int - monthly_cost_other_loans
		'''
		return self._incomeinfo

	@property
	def shipinfo(self):
		''' Shipment info used in the transaction

			Available named values are:
			* int - delay_adjust
			* str - shipping_company
			* str - shipping_product
			* dict - warehouse_addr
		'''
		return self._shipinfo

	@property
	def travelinfo(self):
		''' Travel info used in the transaction

			Available named values are:
			* string - travel_company
			* string - reseller_company
			* string - departure_date
			* string - return_date
			* array  - destinations
			* array  - passenger_list
			* array  - passport_no
			* array  - driver_license_no
		'''
		return self._travelinfo

	@property
	def clientip(self):
		''' IP address of the client
			populated by parse_wsgi_environment '''
		if self.use_x_forwarded_for and self._xfwd_addr is not None:
			return self._xfwd_addr
		if self._client_addr is None:
			raise AttributeError("clientip")
		return self._client_addr

	@clientip.setter
	def clientip(self, value):
		self._client_addr = value

	def __init__(self, config):
		''' Creates the Klarna Object, to complete initialisation init() should also
			be called which will create the XML-RPC object

			config a klarna.Config object (or any other object implementing the
				mapping protocol) containing the configuration options to use

			required fields of the config object
			* eid
			* secret
			* pcstorage
			* pcuri
		'''

		self.config = config

		# Get XML-RPC server settings
		self.addr, server_settings = self.servers[config.get('mode', 'beta')]
		self.scheme = server_settings.get('scheme', 'https')
		if 'port' in server_settings:
			self.port = server_settings['port']
		else:
			self.port = self.default_ports[self.scheme]

		# Should candice statistics collection be used?
		self.candice = config.get('candice', False)

		# PClass settings
		self.pcstorage = config['pcstorage']
		self.pcuri = config['pcuri']

		# Wrappers with a reference to this object
		self.OCR = partial(self.OCR, klarna=self)
		self.INVNO = partial(self.INVNO, klarna=self)
		self.CUSTNO = partial(self.CUSTNO, klarna=self)
		self.PNO = partial(self.PNO, klarna=self)
		self.RNO = partial(self.RNO, klarna=self)

		# Create empty containers
		self.clear()

	def init(self):
		''' Initialises the XML-RPC object according to the configuration '''

		# splice port number into url
		addr = self.addr.split('/', 1)
		url = '%s://%s:%s/%s' % (self.scheme, addr[0], self.port,
			addr[1] if len(addr) > 1 else '')

		# Create ServerProxy object
		logger.info('Using XML-RPC server @ %s', url)
		self.xmlrpc = ServerProxy(url,
			verbose=self.config.get('dumpxml', False))

		# Attach candice logging if requested
		if self.candice:
			self.xmlrpc.candice = Candice(self.c_addr, self.c_port,
				self.eid, self.secret, url)

	@remote_call
	def fetch_pclasses(self, country=None, language=None, currency=None):
		''' Fetches the PClasses from Klarna, removes the cached/stored pclasses
			and updates.
			this method should only be called once!
		'''

		if country is None:
			country = self.country
		if language is None:
			language = self.language
		if currency is None:
			currency = self.currency

		if isinstance(self.pclasses, pclasses.PCStorage):
			# Already called
			logger.debug("fetch_pclasses already called, skipped")
			return

		# Save to local name to avoid having a broken pclass storage saved
		storage = self.get_pcstorage()

		# Attempt to load previously stored pclasses, so they aren't accidentially
		# removed
		try:
			storage.load(self.pcuri)
		except:
			logger.warning("Failed to load pclasses", exc_info=True)

		# Calculate digest
		digest = get_digest(':'.join(
			[str(self.eid), str(Currencies[currency]), self.secret]))

		# Make the call
		result = self.xmlrpc.get_pclasses(self.PROTO, self.VERSION, self.eid,
			Currencies[currency], digest, Countries[country], Languages[language])

		for pclass in result:
				pclass = PClass(
					pclass[0],
					pclass[1],
					pclass[2],
					float(pclass[3]) / 100,
					float(pclass[4]) / 100,
					float(pclass[5]) / 100,
					float(pclass[6]) / 100,
					pclass[7],
					pclass[8],
					pclass[9],
					self.eid)
				storage.add_pclass(pclass)

		storage.save(self.pcuri)

		# Everyhing went fine, set storage on object
		self.pclasses = storage

	def get_pcstorage(self):
		storage = self.pcstorage
		if isinstance(storage, type) and issubclass(storage, pclasses.PCStorage):
			return storage()
		return pclasses.get_pclass_storage(storage)

	def clear_pclasses(self):
		''' Removes the stored PClasses '''

		if not isinstance(self.pclasses, pclasses.PCStorage):
			self.pclasses = self.get_pcstorage()
		self.pclasses.clear(self.pcuri)
		self.pclasses = None

	def get_pclass(self, id):
		''' Returns the specified PClass. '''

		check_type('PClass ID', id, (int,))

		# Load pclasses if needed
		if not isinstance(self.pclasses, pclasses.PCStorage):
			self.pclasses = self.get_pcstorage()
			self.pclasses.load(self.pcuri)

		# Query storage for pclass with given id and configured eid
		return self.pclasses.get_pclass(id, self.eid)

	def get_pclasses(self, type=None):
		''' Retrieves the specified PClasses

			Type can be any of the values in klarna.PClass.Type
		'''

		# Load pclasses if needed
		if not isinstance(self.pclasses, pclasses.PCStorage):
			self.pclasses = self.get_pcstorage()
			self.pclasses.load(self.pcuri)

		pcls = self.pclasses.get_pclasses(self.country, type)
		pcls = list(pcls[self.eid].values())
		pcls.sort()
		return pcls

	@remote_call
	def check_ilt(self, amount, pno, gender, encoding=None):
		''' The purpose of this method is to check if the customer has
			answered the ILT questions. If the questions needs to be answered,
			an list will be returned with ILTQuestion objects.

			The answers should then be passed using set_income_info when
			calling reserve_amount/add_transaction. Using the key member
			of the question object as key and the answer from the customer as
			value.

			Note: You need to set shipping address before calling this method.

			amount: Amount including VAT
			pno: Personal number, SSN, date of birth, etc
			gender: Gender.MALE or Gender.FEMALE or None for unspecified
			encoding: Encoding constant for the PNO parameter.

		'''

		from . import ilt

		amount = fix_amount(amount)

		# Check pno syntax
		if encoding is None:
			encoding = self.get_pno_encoding()
		self.check_pno(pno, encoding)

		# Check gender
		if gender is None:
			gender = ''
		elif not isinstance(gender, int):
			gender = GenderMap[gender]

		# Check/Convert Addresses
		shipping = self.assemble_addr(self.shipping)

		# Make sure shipping country and set country match
		if shipping['country'] != Countries[self.country]:
			raise ShippingCountryMismatch(shipping['country'], self.country)

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), pno, self.secret]))

		# Make call
		result = self.xmlrpc.check_ilt(self.PROTO, self.VERSION,
			self.eid, digest, amount, pno, gender, shipping,
			Countries[self.country], Languages[self.language],
			Currencies[self.currency], Encoding[encoding])

		return [ilt.Question(k, v['type'], v['text'], v['values'])
			for (k, v) in result.items()]

	@remote_call
	def get_addresses(self, pno, encoding=None, type=GetAddressFlag.GIVEN):
		''' The get_addreses function is used to retrieve a customers adress(es).
			Using this, the customer is not required to enter any information only
			confirm the one presented to him/her.

			The get_adresses function can also be used for companies.
			If the customer enters a company number, it will return all the addresses
			where the company is registered at.

			The get_addresses function is ONLY allowed to be used for Swedish persons
			with the following conditions:
			* It can only be used if invoice or part payment is the default payment
				method.
			* It has to disappear if the customer chooses another payment method
			* The button is not allowed to be called "get address", but "continue" or
				it can be picked up automatically when all the numbers have been typed.

			http://integration.klarna.com/en/api/standard-integration/functions/\
getaddresses
		'''

		if self.country not in ('SE',):
			msg = "This method is only available for Swedish customers."
			raise KlarnaException(msg)

		# Check pno syntax
		if encoding is None:
			encoding = self.get_pno_encoding()
		self.check_pno(pno, encoding)

		# Make call
		digest = get_digest(':'.join((str(self.eid), pno, self.secret)))
		result = self.xmlrpc.get_addresses(self.PROTO, self.VERSION, pno, self.eid,
			digest, Encoding[encoding], type, self.clientip)

		def build_addr(data):
			addr = Address()

			if type == GetAddressFlag.GIVEN:
				addr.is_company = True if len(data) == 5 else False
				if addr.is_company:
					(addr.company, addr.street, addr.zip, addr.city, addr.country) = data
				else:
					(addr.fname, addr.lname, addr.street, addr.zip, addr.city,
						addr.country) = data

			elif type == GetAddressFlag.LAST:
				# Here we cannot decide if it is a company or not? Assume private person.
				addr.is_company = False
				addr.lname, addr.street, addr.zip, addr.city, addr.country = data

			elif type == GetAddressFlag.ALL:
				if len(data[0]) > 0:
					addr.fname, addr.lname = data[:2]
				else:
					# Empty fname, assume it's a company
					addr.is_company = True
					addr.company = data[1]
				addr.street, addr.zip, addr.city, addr.country = data[2:]

			return addr

		# Create Addr objects from result set
		return [build_addr(data) for data in result]

	@remote_call
	def invoice_address(self, invno):
		''' Retrieves the address used for an active invoice
			returns a Addr containing the address
		'''

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), invno, self.secret]))

		# Make call
		result = self.xmlrpc.invoice_address(self.PROTO, self.VERSION, self.eid,
			invno, digest)

		addr = Address()
		if len(result[0]) > 0:
			addr.is_company = False
			addr.fname, addr.lname = result[:2]
		else:
			# Empty fname, assume it's a company
			addr.is_company = True
			addr.company = result[0]
		addr.street, addr.zip, addr.city, addr.country = result[2:]

		return addr

	@remote_call
	def invoice_amount(self, invno):
		''' Retrieves the total amount for an active invoice.
			returns the total amount as float
		'''

		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), invno, self.secret]))

		# Make call
		result = self.xmlrpc.invoice_amount(self.PROTO, self.VERSION, self.eid,
			invno, digest)

		return result / 100.0

	@remote_call
	def update_orderno(self, invno, orderid):
		''' Changes the order number of a purchase that was set when the order was
			made online.

			returns the invoice number
		'''

		check_type('Order number', orderid, (basestring,))
		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)

		# Calculate digest
		digest = get_digest(':'.join([invno, orderid, self.secret]))

		# Make the call
		result = self.xmlrpc.update_orderno(self.PROTO, self.VERSION, self.eid,
			digest, invno, orderid)

		return self.INVNO(result)

	@remote_call
	def email_invoice(self, invno):
		''' Sends an activated invoice to the customer via e-mail.
			The email is sent in plain text format and contains a link to a PDF-invoice.

			returns the invoice number
		'''

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), invno, self.secret]))

		# Make the call
		result = self.xmlrpc.email_invoice(self.PROTO, self.VERSION, self.eid,
			invno, digest)

		return self.INVNO(result)

	@remote_call
	def send_invoice(self, invno):
		''' Requests a postal send-out of an activated invoice to a customer by
			Klarna (charges may apply)

			returns the invoice number
		'''

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), invno, self.secret]))

		# Make the call
		result = self.xmlrpc.send_invoice(self.PROTO, self.VERSION, self.eid,
			invno, digest)

		return self.INVNO(result)

	@remote_call
	def update_goods_qty(self, invno, artno, qty):
		''' Changes the quantity of a specific item in a passive invoice.
			return the invoice number
		'''

		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)
		check_type('Article Number', artno, (basestring,))
		check_type('Quantity', qty, (int,))

		# Calcualte digest
		digest = get_digest(':'.join([invno, artno, str(qty), self.secret]))

		# Make the call
		result = self.xmlrpc.update_goods_qty(self.PROTO, self.VERSION, self.eid,
			digest, invno, artno, qty)

		return self.INVNO(result)

	@remote_call
	def update_charge_amount(self, invno, type, amount):
		''' Changes the amount of a fee (e.g. the invoice fee) in a passive invoice.
			returns the invoice number.

		'''

		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)
		check_type('Amount', amount, (int, float))
		check_type('Fee type', type, (int,))
		amount = fix_amount(amount)

		# Calculate digest
		digest = get_digest(':'.join([invno, str(type), str(amount), self.secret]))

		# Make the call
		try:
			result = self.xmlrpc.update_charge_amount(self.PROTO, self.VERSION,
				self.eid, digest, invno, type, amount)
		except xmlrpc.ProtocolError as e:
			# re-raise as klarna exception
			# shadows any real http errors
			raise UnknownFee(type, root_cause=e)

		return self.INVNO(result)

	def add_article(self, qty=None, artno='', title='', price=None, vat=None,
			discount=0, flags=Flag.INC_VAT, **kwargs):
		''' Adds an article to the current goods list for the current order.

			Note: It is recommended that you use GoodIs.INC_VAT in flags

			Flags can be:
			GoodsIs.INC_VAT
			GoodsIs.SHIPPING
			GoodsIs.HANDLNIG
			GoodsIs.PRINT1000
			GoodsIs.PRINT100
			GoodsIs.PRINT10
		'''

		# Verify input
		check_type('Quantity', qty, (int,))
		check_type('Price', price, (int, float))
		check_type('VAT', vat, (int, float))
		check_type('Discount', discount, (int, float))

		if not artno and not title:
			raise KlarnaException("Title or artNo needs to be set")

		# Append article dictionary to goods list
		if not hasattr(self, 'goodslist'):
			self.goodslist = []

		article = {
			'artno': str(artno),
			'title': title,
			'price': fix_amount(price),
			'vat': vat,
			'discount': discount,
			'flags': flags}

		self.goodslist.append({'goods': article, 'qty': qty})
		logger.debug("article added %s", article)

	def add_art_no(self, qty=None, artno=None, **kwargs):
		''' adds an article number and quantity to be used in activate_part,
			credit_part or invoice_part_amount
		'''

		check_type('Quantity', qty, (int,))

		if not hasattr(self, 'artnos'):
			self.artnos = []

		self.artnos.append({'artno': str(artno), 'qty': qty})

	@remote_call
	def add_transaction(self, pno, gender, flags=0, pclass=-1, encoding=None,
			clear=True):
		''' Assemble and send the current order to Klarna
			This clears all order data unless clear is set to False.

			returns a tuple with invoice number and Order status flag or raises
			a xmlrpc.Fault exception.

			If the flag Flag.RETURN_OCR is used the returned tuple will be
			(Invoice Number, OCR Number, Order Status flag)

			Gender is only required for Germany and Netherlands.

			Flags can be:
			* Flag.TEST_MODE
			* Flag.AUTO_ACTIVATE
			* Flag.PRE_PAY
			* Flag.SENSITIVE_ORDER
			* Flag.RETURN_OCR
			* Flag.MOBILEPHONE_TRANSACTION
			* Flag.SEND_PHONE_PIN

			Note:
			Normal shipment is assumed unless otherwise specified, you can do this by
			calling	set_shipment_info(delay_adjust=...)
			with either value from ShipmentType

			http://integration.klarna.com/en/api/standard-integration/functions/\
addtransaction
		'''

		check_type('PNO/SSN', pno, (basestring,), Klarna.PNO)

		if gender is None:
			gender = ''

		# Check pno syntax
		if encoding is None:
			encoding = self.get_pno_encoding()
		self.check_pno(pno, encoding)

		# Check that there is articles for this transaction
		if not hasattr(self, 'goodslist'):
			raise MissingGoodsList()
		if len(self.goodslist) < 1:
			raise EmptyGoodsList()

		# Check/Convert Addresses
		billing = self.assemble_addr(self.billing)
		shipping = self.assemble_addr(self.shipping)

		# Assume normal shipment unless otherwise specified
		if 'delay_adjust' not in self.shipinfo:
			self.shipinfo['delay_adjust'] = ShipmentType.NORMAL

		# Make sure shipping country and set country match
		if shipping['country'] != Countries[self.country]:
			raise ShippingCountryMismatch(shipping['country'], self.country)

		# Calculate digest
		digest = get_digest(':'.join(
			[goods['goods']['title'] for goods in self.goodslist] + [self.secret]))

		# Make call
		result = self.xmlrpc.add_invoice(self.PROTO, self.VERSION,
			pno,
			gender,
			self.reference,
			self.reference_code,
			self.orderid[0],
			self.orderid[1],
			shipping,
			billing,
			self.clientip,
			flags,
			Currencies[self.currency],
			Countries[self.country],
			Languages[self.language],
			self.eid,
			digest,
			Encoding[encoding],
			pclass,
			self.goodslist,
			self.comment,
			self.shipinfo,
			self.travelinfo,
			self.incomeinfo,
			self.bankinfo,
			self.sid,
			self.extrainfo)

		if clear:
			self.clear()

		return result

	@remote_call
	def has_account(self, pno, encoding=None):
		''' Checks if the specified SSN/PNO has an part payment account with Klarna.

			http://integration.klarna.com/en/api/standard-integration/functions/\
hasaccount
		'''

		check_type('PNO/SSN', pno, (basestring,), Klarna.PNO)

		# Check pno syntax
		if encoding is None:
			encoding = self.get_pno_encoding()
		self.check_pno(pno, encoding)

		# Calculate digest
		digest = get_digest(':'.join((str(self.eid), pno, self.secret)))

		# Make the call
		result = self.xmlrpc.has_account(self.PROTO, self.VERSION, self.eid, pno,
			digest, Encoding[encoding])

		# Convert result to proper python type
		return {'true': True, 'false': False}[result]

	@remote_call
	def check_order_status(self, id, type=None):
		''' Returns the current order status for a specific reservation or invoice
			Use this when add_transaction or reserve_amount returns OrderStatus.PENDING

			Order status can be:
			OrderStatus.ACCEPTED
			OrderStatus.PENDING
			OrderStatus.DENIED

			http://integration.klarna.com/en/api/other-functions/functions/\
checkorderstatus
		'''

		if type is not None:
			if type is OrderStatusFor.INVOICE:
				check_type('Invoice Number', id, (basestring,), Klarna.INVNO)
			elif type is OrderStatusFor.RESERVATION:
				check_type('Reservation Number', id, (basestring,), Klarna.RNO)
		else:
			if isinstance(id, Klarna.INVNO):
				type = OrderStatusFor.INVOICE
			elif isinstance(id, Klarna.RNO):
				type = OrderStatusFor.RESERVATION
			else:
				# Default to invoice
				type = OrderStatusFor.INVOICE

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), id, self.secret]))

		# Make the call
		result = self.xmlrpc.check_order_status(self.PROTO, self.VERSION, self.eid,
			digest, id, int(type))

		return result

	@remote_call
	def activate_invoice(self, invno, pclass=-1, clear=True):
		''' Activates previously created invoice by add_transaction

			Note:
			If you want to change shipment type, you can specify it using
			set_shipment_info(delay_adjust=...)
			with either value from ShipmentType

			returns a url to PDF of the activated invoice

			http://integration.klarna.com/en/api/standard-integration/functions/\
activateinvoice
		'''

		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)

		# Assume normal shipment unless otherwise specified
		if 'delay_adjust' not in self.shipinfo:
			self.shipinfo['delay_adjust'] = ShipmentType.NORMAL

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), invno, self.secret]))

		# Make call
		result = self.xmlrpc.activate_invoice(self.PROTO, self.VERSION, self.eid,
			invno, digest, pclass, self.shipinfo)

		if clear:
			self.clear()

		return result

	@remote_call
	def delete_invoice(self, invno):
		''' Removes a passive invoices which has previously been created by
			add_transaction,

			Returns True if the invoice was successfully removed, otherwise
			an xmlrpc.Fault is raised.
		'''

		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), invno, self.secret]))

		# Make call
		result = self.xmlrpc.delete_invoice(self.PROTO, self.VERSION, self.eid,
			invno, digest)

		return result == 'ok'

	@remote_call
	def reserve_amount(self, pno, gender, amount=None, flags=0, pclass=-1,
			encoding=None, clear=True):
		''' Reserves a purchase amount for a specific customer.
			the reservation is valid, by default, for 7 days.

			Returns a tuple with reservation number and order status flag or
			a xmlrpc.Fault is raised.

			Note:
			Activation must be done with activate_reservation, you can not activate
			through Klarna Online.

			Gender is only required for Germany and the Netherlands.

			pno: Personal number, SSN, date of birth etc
			gender: Gender.MALE, Gender.FEMALE or None
			amount: The amount to be reserved
			flags: Options which affect the behaviour
			pclass: pclass name
			encoding: PNO encoding
			clear: Whether customer info should be cleared after this call

			Flags can be set to:
			* Flag.TEST_MODE
			* Reserve.SENSITIVE_ORDER
			* Reserve.PHONE_TRANSACTION
			* Reserve.SEND_PHONE_PIN

			http://integration.klarna.com/en/api/advanced-integration/functions/\
reserveamount
		'''

		if gender is None:
			gender = ''

		country = self.country
		language = self.language
		currency = self.currency

		check_type('PNO/SSN', pno, (basestring,), Klarna.PNO)
		check_type('Flags', flags, (int,))

		if not hasattr(self, 'goodslist'):
			raise MissingGoodsList()
		if len(self.goodslist) < 1:
			raise EmptyGoodsList()

		if amount == None:
			# Calculate amount from goodslist
			amount = sum([(g['goods']['price'] * g['qty']) for g in self.goodslist])
			amount = int(amount)
		else:
			check_type('Amount', amount, (int, float))
			amount = fix_amount(amount)

		if amount <= 0:
			raise InvalidAmount(amount)

		# Check pno syntax
		if encoding is None:
			encoding = self.get_pno_encoding()
		self.check_pno(pno, encoding)

		# Check/Convert Addresses
		billing = self.assemble_addr(self.billing)
		shipping = self.assemble_addr(self.shipping)

		# Make sure shipping country and set country match
		if shipping['country'] != Countries[self.country]:
			raise ShippingCountryMismatch(shipping['country'], self.country)

		# Assume normal shipment unless otherwise specified
		if 'delay_adjust' not in self.shipinfo:
			self.shipinfo['delay_adjust'] = ShipmentType.NORMAL

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), pno, str(amount), self.secret]))

		# Make call
		result = self.xmlrpc.reserve_amount(self.PROTO, self.VERSION, pno, gender,
			amount, self.reference, self.reference_code, self.orderid[0],
			self.orderid[1], shipping, billing, self.clientip, flags,
			Currencies[self.currency], Countries[self.country],
			Languages[self.language], self.eid, digest, Encoding[encoding],
			pclass, self.goodslist, self.comment, self.shipinfo,
			self.travelinfo, self.incomeinfo, self.bankinfo, self.sid, self.extrainfo)

		if clear:
			self.clear()

		return result

	@remote_call
	def cancel_reservation(self, rno):
		''' Cancels a reservation
			returns True if the reservation was successfully canceled else
			raises a xmlrpc.Fault

			rno: Reservation number

			http://integration.klarna.com/en/api/advanced-integration/functions/\
cancelreservation
		'''

		check_type('Reservation number', rno, (basestring,), Klarna.RNO)

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), rno, self.secret]))

		# Make call
		result = self.xmlrpc.cancel_reservation(self.PROTO, self.VERSION, rno,
			self.eid, digest)

		return result == 'ok'

	@remote_call
	def change_reservation(self, rno, amount, flags=Flag.NEW_AMOUNT):
		''' Changes the specified reservation to a new amount
			returns True

			rno:	Reservation number
			amount:	Amount including VAT
			flags:	Options which affect the behaviour

			Flags can be set to:
			Flag.NEW_AMOUNT
			Flag.ADD_AMOUNT

			http://integration.klarna.com/en/api/advanced-integration/functions/\
changereservation
		'''

		check_type('Reservation number', rno, (basestring,), Klarna.RNO)
		check_type('Amount', amount, (int, float))
		check_type('Flags', flags, (int,))

		amount = fix_amount(amount)
		if amount <= 0:
			raise InvalidAmount(amount)

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), rno, str(amount), self.secret]))

		# Make call
		result = self.xmlrpc.change_reservation(self.PROTO, self.VERSION, rno,
			amount, self.eid, digest, flags)

		return result == 'ok'

	@remote_call
	def activate_reservation(self, pno, rno, gender, ocr='', flags=0, pclass=-1,
			encoding=None, clear=True):
		''' Activates a previously created reservation.

			returns a tuple with:
				Risk status ("no_risk", "ok")
				Invoice number

			Gender is only required for Germany and the Netherlands.

			Note:
			Normal shipment is assumed unless otherwise specified, you can do this by
			calling	set_shipment_info(delay_adjust=...)
			with either value from ShipmentType

			pno:		Personal number, SSN, date of birth, etc.
			rno:		Reservation number.
			gender:		'MALE, 'FEMALE' or None
			ocr:		A OCR number.
			flags:		Options which affect the behaviour.
			pclass:		pclass name
			encoding:	PNO encoding
			clear:		Whether customer info should be cleared after this call.

			Flags can be set to:
			Flag.TEST_MODE
			Reserve.SEND_BY_MAIL
			Reserve.SEND_BY_EMAIL
			Reserve.PRESERVE_RESERVATION
			Reserve.SENSITIVE_ORDER

			http://integration.klarna.com/en/api/advanced-integration/functions/\
activatereservation
		'''

		if gender is None:
			gender = ''

		country = self.country
		language = self.language
		currency = self.currency

		check_type('PNO/SSN', pno, (basestring,), Klarna.PNO)
		check_type('Reservation number', rno, (basestring,), Klarna.RNO)
		check_type('Flags', flags, (int,))

		if not hasattr(self, 'goodslist'):
			raise MissingGoodsList()
		if len(self.goodslist) < 1:
			raise EmptyGoodsList()

		# Check pno syntax
		if encoding is None:
			encoding = self.get_pno_encoding()
		self.check_pno(pno, encoding)

		# Check/Convert Addresses
		billing = self.assemble_addr(self.billing)
		shipping = self.assemble_addr(self.shipping)

		# Assume normal shipment unless otherwise specified
		if 'delay_adjust' not in self.shipinfo:
			self.shipinfo['delay_adjust'] = ShipmentType.NORMAL

		# Make sure shipping country and set country match
		if shipping['country'] != Countries[self.country]:
			raise ShippingCountryMismatch(shipping['country'], self.country)

		# Calculate digest
		digest = get_digest(':'.join(
			[str(self.eid), pno] +
			['%s:%s' % (g['goods']['artno'], g['qty']) for g in self.goodslist] +
			[self.secret]))

		# Make call
		result = self.xmlrpc.activate_reservation(self.PROTO, self.VERSION,
			rno,
			ocr,
			pno,
			gender,
			self.reference,
			self.reference_code,
			self.orderid[0],
			self.orderid[1],
			shipping,
			billing,
			self.clientip,
			flags,
			Currencies[self.currency],
			Countries[self.country],
			Languages[self.language],
			self.eid,
			digest,
			Encoding[encoding],
			pclass,
			self.goodslist,
			self.comment,
			self.shipinfo,
			self.travelinfo,
			self.incomeinfo,
			self.bankinfo,
			self.extrainfo)

		if clear:
			self.clear()

		risk, invno = result
		return (risk, self.INVNO(invno))

	@remote_call
	def split_reservation(self, rno, amount, flags=0):
		''' Splits a reservation due to for example outstanding articles.
			returns the new reservation number.

			For flags usage see reserve_amount

			rno:		Reservation number
			amount:		The amount to be subtracted from the reservation.
			flags:		Options which affect the behaviour.

			http://integration.klarna.com/en/api/advanced-integration/functions/\
splitreservation
		'''
		check_type('Reservation number', rno, (basestring,), Klarna.RNO)
		check_type('Amount', amount, (int, float))
		check_type('Flags', flags, (int,))

		amount = fix_amount(amount)
		if amount <= 0:
			raise InvalidAmount(amount)

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), rno, str(amount), self.secret]))

		# Make call
		result = self.xmlrpc.split_reservation(self.PROTO, self.VERSION, rno, amount,
			self.orderid[0], self.orderid[1], flags, self.eid, digest)

		return self.RNO(result)

	@remote_call
	def activate_part(self, invno, pclass=-1, clear=True):
		''' Partially activates a passive invoice

			returns a dictionary with 'url' and 'invno'
			the value of url points to a pdf-version of the activated invoice.
			the value of invno is the number on the new passive invoice, or 0 if
			the entire invoice was activated.

			Note:
			You need to call add_artno first, to specify which articles and how many
			you want to activate.

			If you want to change shipment type, you can specify it using
			set_shipment_info(delay_adjust=...)
			with either value from ShipmentType
		'''

		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)

		if not hasattr(self, 'artnos'):
			raise MissingArtNos()
		if len(self.artnos) < 1:
			raise EmptyArtNos()

		# Assume normal shipment unless otherwise specified
		if 'delay_adjust' not in self.shipinfo:
			self.shipinfo['delay_adjust'] = ShipmentType.NORMAL

		# Calculate digest
		digest = get_digest(':'.join(
			[str(self.eid), invno] +
			['%s:%s' % (artno['artno'], artno['qty']) for artno in self.artnos] +
			[self.secret]))

		# Make call
		result = self.xmlrpc.activate_part(self.PROTO, self.VERSION, self.eid, invno,
			self.artnos, digest, pclass, self.shipinfo)

		if clear:
			self.clear()

		if 'invno' in result:
			result['invno'] = self.INVNO(result['invno'])
		return result

	@remote_call
	def credit_part(self, invno, credno=''):
		''' Performs a partial refund on an invoice, part payment or mobile purchase.
			returns invoice number

			Note:
			You need to call add_artno first

			http://integration.klarna.com/en/api/invoice-handling-functions/functions/\
creditpart
		'''

		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)
		check_type('Credit number', credno, (basestring, int))

		if not hasattr(self, 'artnos'):
			raise MissingArtNos()
		if len(self.artnos) < 1:
			raise EmptyArtNos()

		# Calculate digest
		digest = get_digest(':'.join(
			[str(self.eid), invno] +
			['%s:%s' % (artno['artno'], artno['qty']) for artno in self.artnos] +
			[self.secret]))

		# Make call
		result = self.xmlrpc.credit_part(self.PROTO, self.VERSION, self.eid, invno,
			self.artnos, credno, digest)

		return self.INVNO(result)

	@remote_call
	def return_amount(self, invno, amount, vat, flags=Flag.INC_VAT):
		''' Gives discounts on invoicers
			returns invoice number

			If you are using standard integration and the purchase is not yet activated
			(you have not yet delivered the goods), just change the article list in our
			online interface Klarna Online.

			Flags can be:
			GoodsIs.INC_VAT

			invno: Invoice number
			amount: The amount given as a discount
			vat: VAT percent as float

			http://integration.klarna.com/en/api/invoice-handling-functions/functions/\
returnamount
		'''

		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)
		check_type('Amount', amount, (int, float))
		check_type('VAT', vat, (int, float))
		check_type('Flags', flags, (int,))

		amount = fix_amount(amount)
		#if amount <= 0:
		#	raise KlarnaException("Amount needs to be larger than 0! (%s)" % amount)

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), invno, self.secret]))

		# Make the call
		result = self.xmlrpc.return_amount(self.PROTO, self.VERSION, self.eid, invno,
			amount, vat, digest, flags)

		return self.INVNO(result)

	@remote_call
	def credit_invoice(self, invno, credno=''):
		''' Performs a complete refund on an invoice, part payment and mobile
			purchase.

			returns the invoice number

			invno: Invoice Number
			credno: Credit number

			http://integration.klarna.com/en/api/invoice-handling-functions/functions/\
creditinvoice
		'''

		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)
		check_type('credno', credno, (basestring,))

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), invno, self.secret]))

		# Make the call
		result = self.xmlrpc.credit_invoice(self.PROTO, self.VERSION, self.eid,
			invno, credno, digest)

		return self.INVNO(result)

	@remote_call
	def invoice_part_amount(self, invno):
		''' Retrieves the amount of a specific goods from a purchase.

			Note:
			You need to call add_artno first.

			invno: Invoice number

			http://integration.klarna.com/en/api/other-functions/functions/\
invoicepartamount
		'''

		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)

		if not invno:
			raise KlarnaException('Invoice number not set')

		if not hasattr(self, 'artnos'):
			raise MissingArtNos()
		if len(self.artnos) < 1:
			raise EmptyArtNos()

		# Calculate digest
		digest = get_digest(':'.join(
			[str(self.eid), invno] +
			['%s:%s' % (artno['artno'], artno['qty']) for artno in self.artnos] +
			[self.secret]))

		# Make call
		result = self.xmlrpc.invoice_part_amount(self.PROTO, self.VERSION, self.eid,
			invno, self.artnos, digest)

		return result / 100.0

	@remote_call
	def reserve_OCR(self, count, country=None):
		''' Reserves a specified number of OCR numbers for the specified country
			or the configured country of this object.

			returns a list of OCR numbers.

			count: The number of OCR numbers to reserve
			country: country code of country to reserve OCR numbers for

			http://integration.klarna.com/en/api/advanced-integration/functions/\
reserveocrnums
		'''

		check_type('Count', count, (int,))

		if country is None:
			country = self.country

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), str(count), self.secret]))

		# Make the call
		result = self.xmlrpc.reserve_ocr_nums(self.PROTO, self.VERSION, count,
			self.eid, digest, Countries[country])

		return [self.OCR(s) for s in result]

	@remote_call
	def reserve_OCR_email(self, count, email, country=None):
		''' Reserves the number of OCRs specified and sends them to the given email.
			returns True if the OCRs were created and sent.
		'''

		check_type('Count', count, (int,))
		self.check_email(email)

		if country is None:
			country = self.country

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), str(count), self.secret]))

		# Make the call
		result = self.xmlrpc.reserve_ocr_nums_email(self.PROTO, self.VERSION, count,
			email, self.eid, digest, Countries[country])

		return result == 'ok'

	@remote_call
	def get_customer_no(self, pno, encoding=None):
		''' Retrieves a list of all the customer numbers associated with the
			specified pno.

			returns list containing all customer numbers associated with that pno.
		'''

		check_type('PNO/SSN', pno, (basestring,), Klarna.PNO)

		# Check pno syntax
		if encoding is None:
			encoding = self.get_pno_encoding()
		self.check_pno(pno, encoding)

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), pno, self.secret]))

		# Make the call
		result = self.xmlrpc.get_customer_no(self.PROTO, self.VERSION, pno, self.eid,
			digest, Encoding[encoding])

		return [self.CUSTNO(r) for r in result]

	@remote_call
	def set_customer_no(self, pno, custno, encoding=None):
		''' Associates a pno with a customer number when you want to make future
			purchases without a pno.

			returns True
		'''

		check_type('PNO/SSN', pno, (basestring,), Klarna.PNO)

		# Check pno syntax
		if encoding is None:
			encoding = self.get_pno_encoding()
		self.check_pno(pno, encoding)

		if not custno:
			raise MissingCustomerNumber()

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), pno, custno, self.secret]))

		# Make the call
		result = self.xmlrpc.set_customer_no(self.PROTO, self.VERSION, pno, custno,
			self.eid, digest, Encoding[encoding])

		return result == 'ok'

	@remote_call
	def remove_customer_no(self, custno):
		''' Removes a customer number from association with a pno.
			returns True
		'''

		if not custno:
			raise MissingCustomerNumber()

		# Calculate digest
		digest = get_digest(':'.join([str(self.eid), custno, secret]))

		# Make the call
		result = self.xmlrpc.remove_customer_no(self.PROTO, self.VERSION, custno,
			eid, digest)

		return result == 'ok'

	@remote_call
	def update_email(self, pno, email, encoding=None):
		''' Updates email on all invoices (and reservations?) for specified pno and
			store/eid.

			pno:	Social security number, Personal Number, etc
			email:	Email address

			returns True
		'''

		check_type('PNO/SSN', pno, (basestring,), Klarna.PNO)

		# Check pno syntax
		if encoding is None:
			encoding = self.get_pno_encoding()
		self.check_pno(pno, encoding)

		self.check_email(email)

		# Calculate digest
		digest = get_digest(':'.join([pno, email, self.secret]))

		# Make the call
		result = self.xmlrpc.update_email(self.PROTO, self.VERSION, self.eid,
			digest, pno, email)

		return result == 'ok'

	@remote_call
	def update_notes(self, invno, notes):
		''' Sets notes/log information for the specified invoice number.
			returns Invoice number
		'''

		check_type('Invoice number', invno, (basestring,), Klarna.INVNO)

		# Calculate digest
		digest = get_digest(':'.join([invno, notes, self.secret]))

		# Make the call
		result = self.xmlrpc.update_notes(self.PROTO, self.VERSION, self.eid, digest,
			invno, notes)

		return self.INVNO(result)

	def get_pno_encoding(self):
		''' Get the PNO/SSn encoding constant for the currently set country
			Raises KlarnaException if currency, country and language doesn't match'''

		ecurr, elang = CountryInfo[self.country]
		if self.currency != ecurr and self.language != elang:
			raise CurrencyLanguageMismatch(self.country, self.currency, self.language)

		return 'PNO_%s' % self.country

	def assemble_addr(self, addr):
		''' Returns a dictionary used to send the address to Klarna '''
		tmp = dict([(k, addr[k]) for k in Address.fields])

		# Required Fields
		if addr.is_company:
			non_empty = ('company', 'email', 'street', 'zip', 'city', 'country')
		else:
			non_empty = ('fname', 'lname', 'email', 'street', 'zip', 'city', 'country')

		for k in non_empty:
			if not tmp[k]:
				# Raise exception with user-friendly name fetched from the property
				# documentation
				raise KlarnaException("%s (%s) not set" % (Address.__dict__[k].__doc__, k))

		# National special rules
		if tmp['country'] in ('NL', 'DE'):
			if not tmp['house_number']:
				raise MissingHouseNumber()

		# Translate symbolic names to IDs
		tmp['country'] = Countries[tmp['country']]
		return tmp

	def clear(self):
		''' Removes all relevant order/customer data from internal structures
		'''

		self.reference = self.reference_code = ''
		self._extrainfo = {}
		self._bankinfo = {}
		self._incomeinfo = {}
		self._travelinfo = {}
		self._shipinfo = {}
		self._comments = []
		self.orderid = ['', '']
		self.sid = {}

		if hasattr(self, '_billing'):
			del self._billing

		if hasattr(self, '_shipping'):
			del self._shipping

		if hasattr(self, 'artnos'):
			del self.artnos

		if hasattr(self, 'goodslist'):
			del self.goodslist

	def check_email(self, email):
		return re.match(Regexp['EMAIL'], email)

	def check_pno(self, pno, encoding):
		regexp = Regexp.get(encoding)
		if regexp is None:
			return
		if re.match(regexp, pno):
			return
		raise KlarnaException("Invalid PNO/SSN")

	def set_comment(self, comment):
		''' Sets the comment, replacing any previous comment '''
		self._comments = [comment]

	def add_comment(self, comment):
		''' Adds a new comment appended to the previous with a newline '''
		self._comments.append(comment)

	def parse_wsgi_env(self, environ):
		''' Collects information from a WSGI environ dictionary.

			ref:
				http://www.python.org/dev/peps/pep-0333/#environ-variables
				http://ken.coar.org/cgi/draft-coar-cgi-v11-03.txt
		'''

		# Required by CGI spec
		ip = environ['REMOTE_ADDR']
		logger.info("using '%s' as remote address" % ip)

		try:
			# Grab the first client ip (the one furthest downstream)
			clients = [c.strip() for c in environ['HTTP_X_FORWARDED_FOR'].split(',')]
			fwd = clients[0]
			logger.info("HTTP_X_FORWARDED_FOR set, using '%s' as forwarded for address"
				% fwd)
		except KeyError:
			fwd = None
		self._client_addr = ip
		self._xfwd_addr = fwd

	def init_checkout(self, session=None):
		''' Initializes the CheckoutHTML objects

			session should be a dictionary-like session object (e.g Session from
			beaker session or pythonweb session)
		'''

		classes = checkout.get_checkout_classes()
		self.co_objects = {}
		for cls in classes:
			obj = cls(self, self.eid, session)
			self.co_objects[obj.ID] = obj

	def get_checkout_html(self, session=None):
		''' Returns the checkout page HTML from the checkout classes

			session should be a dictionary-like session object (e.g Session from
			beaker session or pythonweb session)
		'''

		if self.co_objects is None:
			self.init_checkout(session)

		return '\n'.join(
			[obj.to_html()
				for obj in self.co_objects.values()
				if isinstance(obj, checkout.CheckoutHTML)])

	def set_session_id(self, name, sid):
		''' Sets the session IDs of various device identification and
			behaviour identification software.

			available named session IDs
			* dev_id_1
			* dev_id_2
			* dev_id_3
			* beh_id_1
			* beh_id_2
			* beh_id_3
		'''
		self.sid[name] = sid

	def set_estore_info(self, orderid1='', orderid2='', user=''):
		''' Sets order IDs from other systems for the upcoming transaction
			user is only included with add_transaction call
		'''
		self.extrainfo['estore_user'] = user
		self.orderid = (orderid1, orderid2)

	def set_reference(self, ref, code):
		''' Sets the reference (person) and reference code for the upcoming
			transaction.

			If this is omitted, first name and last name of the submitted company
			address will be used.
		'''
		self.reference = str(ref)
		self.reference_code = code

	def set_shipment_info(self, **kwargs):
		''' Sets the shipment information of the upcoming transaction.
			see shipinfo for available named values
		'''
		self._shipinfo.update(kwargs)

	def set_extra_info(self, **kwargs):
		''' Sets the extra information of the upcoming transaction.
			see extrainfo for available named values
		'''
		self._extrainfo.update(kwargs)

	def set_bank_info(self, **kwargs):
		''' Sets the bank information of the upcoming transaction.
			see bankinfo for available named values
		'''
		self._bankinfo.update(kwargs)

	def set_income_info(self, **kwargs):
		''' Sets the income information of the upcoming transaction.
			see incomeinfo for available named values
		'''
		self._incomeinfo.update(kwargs)

	def set_travel_info(self, **kwargs):
		''' Sets the travel information of the upcoming transaction.
			see shipinfo for available named values
		'''
		self._travelinfo.update(kwargs)

	def get_currency_for_country(self, country):
		''' Get the matching currency constant for the given country '''
		country = lookup(Countries, country)
		return CountryInfo[country][0]

	def get_language_for_country(self, country):
		''' Get the matching language constant for the given country '''
		country = lookup(Countries, country)
		return CountryInfo[country][1]


# Configure XML-RPC Marshaller to marshall the tag objects
d = xmlrpc.Marshaller.dispatch
marshaller = xmlrpc.Marshaller.dump_string
d[Klarna.OCR] = marshaller
d[Klarna.INVNO] = marshaller
d[Klarna.CUSTNO] = marshaller
d[Klarna.PNO] = marshaller
d[Klarna.RNO] = marshaller
