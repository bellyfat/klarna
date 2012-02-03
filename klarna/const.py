''' Klarna API - Constants

Provides constanst used throughout the API
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
# Defines the main API object class used to communicate with Klarna


__reversed = {}


def lookup(mapping, value):
	try:
		# If the value can be converted to int, treat it as a constant
		# else try to use it as a code string
		value = int(value)
	except ValueError:
		value = value.upper()
		# Make sure the code is recognised and return as-is
		if value not in mapping:
			raise ValueError(value)
		return value
	else:
		# Get the reversed mapping
		try:
			r = __reversed[id(mapping)]
		except KeyError:
			r = dict([(v, k) for k, v in mapping.items()])
			__reversed[id(mapping)] = r

		try:
			return r[value]
		except KeyError:
			raise ValueError(value)

version = "2.1.1"


class Page(object):
	CHECKOUT = object()
	PRODUCT = object()


class Order(object):
	INVOICE = 0
	RESERVATION = 1


class ShipmentType(object):
	NORMAL = 1
	EXPRESS = 2


class GoodsIs(object):
	NOFLAG = 0
	PRINT1000 = 1
	PRINT100 = 2
	PRINT10 = 4
	SHIPPING = 8
	HANDLING = 16
	INC_VAT = 32


class Flag(object):
	NOFLAG = 0
	TEST_MODE = 2
	PCLASS_INVOICE = -1
	AUTO_ACTIVATE = 1
	PRE_PAY = 8
	INC_VAT = 32
	SENSITIVE_ORDER = 1024
	RETURN_OCR = 8192
	PHONE_TRANSACTION = 262144
	SEND_PHONE_PIN = 524288

	# Change reservation
	NEW_AMOUNT = 0
	ADD_AMOUNT = 1


class GetAddressFlag(object):
	ALL = 1
	LAST = 2
	GIVEN = 5


class Reserve(object):
	SEND_BY_MAIL = 1 << 2
	SEND_BY_EMAIL = 1 << 3
	PRESERVE = 1 << 4
	SENSITIVE_ORDER = 1 << 5
	PHONE_TRANSACTION = 1 << 8
	SEND_PHONE_PIN = 1 << 9


class OrderStatus(object):
	ACCEPTED = 1
	PENDING = 2
	DENIED = 3


class OrderStatusFor(int):
	pass


OrderStatusFor.INVOICE = OrderStatusFor(0)
OrderStatusFor.RESERVATION = OrderStatusFor(0)
OrderStatusFor.ORDERID = OrderStatusFor(1)


class Gender(object):
	FEMALE = 0
	MALE = 1


GenderMap = {
	'f': Gender.FEMALE,
	'm': Gender.MALE
}


class Fee(object):
	SHIPMENT = 1
	HANDLING = 2

CountryInfo = {
	'DE': ('EUR', 'DE'),
	'DK': ('DKK', 'DA'),
	'FI': ('EUR', 'FI'),
	'NL': ('EUR', 'NL'),
	'NO': ('NOK', 'NB'),
	'SE': ('SEK', 'SV')}

Countries = {
	'DK': 59,
	'FI': 73,
	'DE': 81,
	'NL': 154,
	'NO': 164,
	'SE': 209}

Currencies = {
	'SEK': 0,
	'NOK': 1,
	'EUR': 2,
	'DKK': 3}

Languages = {
	'DA': 27,
	'DE': 28,
	'FI': 37,
	'NB': 97,
	'NL': 101,
	'SV': 138}

# PNO/SSN encoding constants
Encoding = {
	'PNO_SE': 2,
	'PNO_NO': 3,
	'PNO_FI': 4,
	'PNO_DK': 5,
	'PNO_DE': 6,
	'PNO_NL': 7,

	'CUSTNO': 1000,
	'EMAIL': 1001,
	'CELLNO': 1002,
	'BANK_BIC_ACC_NO': 1003}

Regexp = {
	'PNO_SE':
		r'^[0-9]{6,6}(([0-9]{2,2}[-\+]{1,1}[0-9]{4,4})|([-\+]{1,1}[0-9]{4,4})|'
		r'([0-9]{4,6}))$',

	'PNO_NO':
		r'^[0-9]{6,6}((-[0-9]{5,5})|([0-9]{2,2}((-[0-9]{5,5})|([0-9]{1,1})|'
		r'([0-9]{3,3})|([0-9]{5,5))))$',

	'PNO_FI':
		r'^[0-9]{6,6}(([A\+-]{1,1}[0-9]{3,3}[0-9A-FHJK-NPR-Y]{1,1})|([0-9]{3,3}'
		r'[0-9A-FHJK-NPR-Y]{1,1})|([0-9]{1,1}-{0,1}[0-9A-FHJK-NPR-Y]{1,1}))$',

	'PNO_DK':
		r'^[0-9]{8,8}([0-9]{2,2})?$',

	'PNO_DE':
		r'^[0-9]{7,9}$',

	'PNO_NL':
		r'^[0-9]{7,9}$',

	'EMAIL':
		r'^[_a-zA-Z0-9-]+(\.[_a-zA-Z0-9-]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*'
		r'(\.[a-zA-Z0-9-][a-zA-Z0-9-]+)+$',

	'CELLNO':
		r'07[\ \-0-9]{8,13}$'}
