'''Klarna API - Address

Provides Address class which holds a single address of a person or company
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
	basestring = str

__all__ = ('Address',)

from .error import KlarnaException, UnknownCountry
from .const import *

import re


class Address(object):
	fields = ('email', 'telno', 'cellno', 'fname', 'lname', 'company', 'careof',
		'street', 'house_number', 'house_extension', 'zip', 'city', 'country')

	@property
	def email(self):
		'Email address'
		return self._email

	@email.setter
	def email(self, value):
		if re.match(Regexp['EMAIL'], value) is None:
			raise KlarnaException("Invalid E-mail Address")
		self._email = value

	@property
	def telno(self):
		'Phone number'
		return self._telno

	@telno.setter
	def telno(self, value):
		self._telno = value

	@property
	def cellno(self):
		'Cellphone number'
		return self._cellno

	@cellno.setter
	def cellno(self, value):
		self._cellno = value

	@property
	def fname(self):
		'First name'
		return self._fname

	@fname.setter
	def fname(self, value):
		self._fname = value

	@property
	def lname(self):
		'Last name'
		return self._lname

	@lname.setter
	def lname(self, value):
		self._lname = value

	@property
	def company(self):
		'Company name'
		return self._company

	@company.setter
	def company(self, value):
		self.is_company = True
		self._company = value

	@property
	def careof(self):
		'Care of, C/O'
		return self._careof

	@careof.setter
	def careof(self, value):
		self._careof = value

	@property
	def street(self):
		'Street address'
		return self._street

	@street.setter
	def street(self, value):
		self._street = value

	@property
	def zip(self):
		'Zip Code'
		return self._zip

	@zip.setter
	def zip(self, value):
		self._zip = value

	@property
	def city(self):
		'City'
		return self._city

	@city.setter
	def city(self, value):
		if not (isinstance(value, basestring) and len(value) > 0):
			raise KlarnaException("City not specified")
		self._city = value

	@property
	def country(self):
		'Country code'
		return self._country

	@country.setter
	def country(self, value):
		try:
			self._country = lookup(Countries, value)
		except ValueError:
			raise UnknownCountry(value)

	@property
	def house_number(self):
		'House number'
		return self._house_number

	@house_number.setter
	def house_number(self, value):
		self._house_number = value

	@property
	def house_extension(self):
		'House Extension'
		return self._house_extension

	@house_extension.setter
	def house_extension(self, value):
		self._house_extension = value

	def __init__(self, **kwargs):
		self.is_company = False
		for k, v in kwargs.items():
			setattr(self, k, v)

	def __iter__(self):
		for k in self.fields:
			if hasattr(self, k):
				yield k

	def __getitem__(self, key):
		return getattr(self, key, '')

	def __contains__(self, key):
		return getattr(self, key, None)

	def __repr__(self):
		return '(Addr %s)' % ', '.join(
			['%s = %r' %
				(k, getattr(self, k)) for k in self.fields if hasattr(self, k)])
