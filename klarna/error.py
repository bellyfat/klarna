# -*- coding: utf-8 -*-
''' Klarna API - Error

Defines exception subclasses used by Klarna
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


class KlarnaException(Exception):
	''' Exception class used for invalid API usage '''

	message = None
	code = 5000

	def __init__(self, message=None, code=None, root_cause=None):
		if message:
			self.message = message

		if code:
			self.code = code

		self.root_cause = root_cause

	def __str__(self):
		base = '(%d): %s' % (self.code, self.message)
		if self.root_cause is not None:
			return base + '[source %s: %s]' % (type(self.root_cause), self.root_cause)
		return base


class KlarnaValueException(KlarnaException):
	def __init__(self, value, message=None, code=None, root_cause=None):
		KlarnaException.__init__(self,
			message or self.message % value,
			code or self.code,
			root_cause)


class UnknownCountry(KlarnaValueException):
	message = "Unknown Country (%s)"
	code = 5002


class UnknownLanguage(KlarnaValueException):
	message = "Unknown Language (%s)"
	code = 5003


class UnknownCurrency(KlarnaValueException):
	message = "Unknown Currency (%s)"
	code = 5004


class UnknownFee(KlarnaValueException):
	message = "Unknown Fee type (%s)"
	code = 5102


class MissingHouseNumber(KlarnaException):
	message = "House number needs to be specified for Netherlands and Germany"
	code = 50014


class MissingCustomerNumber(KlarnaException):
	message = "customer number not set"
	code = 50050


class MissingArtNos(KlarnaException):
	message = "artNos not specified"
	code = 50063


class MissingGoodsList(KlarnaException):
	message = "Goods list not specified"
	code = 50038


class EmptyArtNos(KlarnaException):
	message = "Empty artNos sequence"
	code = 50064


class EmptyGoodsList(KlarnaException):
	message = 'No articles in goods list'
	code = 50038


class InvalidAmount(KlarnaException):
	message = "Amount needs to be larger than 0! (%s)"
	code = 5100


class MissingXmlRpc(KlarnaException):
	message = 'No XML-RPC object found, have you run Klarna.init()'
	code = 5101


class CurrencyLanguageMismatch(KlarnaException):
	message = "Mismatching currency/language for %s (%s, %s)"
	code = 50024

	def __init__(self, country, currency, language,
			message=None, code=None, root_cause=None):
		KlarnaException.__init__(self,
			message or self.message % (country, currency, language),
			code or self.code,
			root_cause)


class ShippingCountryMismatch(KlarnaException):
	message = "Shipping address country (%s) must match the country set (%s)"
	code = 50041

	def __init__(self, shipping_country, country,
			message=None, code=None, root_cause=None):
		KlarnaException.__init__(self,
			message or self.message % (shipping_country, country),
			code or self.code,
			root_cause)
