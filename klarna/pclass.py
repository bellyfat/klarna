# -*- coding: utf-8 -*-
''' Klarna API - PClass

Defines the class for holding PClasses
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
	long = int

__all__ = ('PClass',)

import time
from .const import *


class PClass(object):
	fields = ('eid', 'id', 'description', 'months', 'startfee', 'invoicefee',
		'interestrate', 'minamount', 'country', 'type', 'expire')

	class Type(object):
		INVOICE = -1
		CAMPAIGN = 0
		ACCOUNT = 1
		SPECIAL = 2
		FIXED = 3
		DELAY = 4
		MOBILE = 5

	@property
	def description(self):
		'Description'
		return self._description

	@description.setter
	def description(self, value):
		self._description = value

	@property
	def months(self):
		'Number of months'
		return self._months

	@months.setter
	def months(self, value):
		if value not in('-', ''):
			self._months = int(value)
		else:
			value = None

	@property
	def startfee(self):
		'Starting fee'
		return self._startfee

	@startfee.setter
	def startfee(self, value):
		self._startfee = float(value)

	@property
	def invoicefee(self):
		'Invoicing/handling fee'
		return self._invoicefee

	@invoicefee.setter
	def invoicefee(self, value):
		self._invoicefee = float(value)

	@property
	def interestrate(self):
		'Interest rate'
		return self._interestrate

	@interestrate.setter
	def interestrate(self, value):
		self._interestrate = float(value)

	@property
	def minamount(self):
		'Minimum amount to use this PClass'
		return self._minamount

	@minamount.setter
	def minamount(self, value):
		self._minamount = int(value)

	@property
	def country(self):
		'Country'
		return self._country

	@country.setter
	def country(self, value):
		try:
			self._country = lookup(Countries, value)
		except ValueError:
			raise UnknownCountry(value)

	@property
	def id(self):
		'ID'
		return self._id

	@id.setter
	def id(self, value):
		self._id = int(value)

	@property
	def type(self):
		'Type'
		return self._type

	@type.setter
	def type(self, value):
		self._type = int(value)

	@property
	def eid(self):
		'Merchant ID or Estore ID connect to this PClass'
		return self._eid

	@eid.setter
	def eid(self, value):
		self._eid = int(value)

	@property
	def expire(self):
		'Valid until/expire unix timestamp'
		return self._expire

	@expire.setter
	def expire(self, value):
		if isinstance(value, (int, long, float)):
			self._expire = value
		elif isinstance(value, basestring) and value not in ('-', ''):
			self._expire = time.mktime(time.strptime(value, '%Y-%m-%d'))
		else:
			self._expire = None

	def is_valid(self, now=None):
		''' True if this PClass is not expired '''

		if getattr(self, 'expire', None) is None:
			# No expire, or unset? assume valid
			return True

		if now is None:
			now = time.time()

		return now < self.expire

	def __init__(self, *args, **kwargs):
		ptk = ('id', 'description', 'months', 'startfee', 'invoicefee',
			'interestrate', 'minamount', 'country', 'type', 'expire', 'eid')

		# Map positional arguments to their respective names
		for k, v in zip(ptk, args):
			kwargs[k] = v

		# Allow desc as a shorthand for description
		if 'desc' in kwargs:
			kwargs['description'] = kwargs['desc']
			del kwargs['desc']

		# Set the attributes
		for k, v in kwargs.items():
			setattr(self, k, v)

	def __lt__(self, other):
		spec = PClass.Type.SPECIAL
		if self.type == spec and other.type != spec:
			return True
		elif self.type != spec and other.type == spec:
			return False

		return self.description < other.description

	def __iter__(self):
		for k in self.fields:
			if k == 'country':
				yield (k, Countries[self.country])
			elif k == 'type':
				yield (k, self.type)
			else:
				yield (k, getattr(self, k, ''))

	def __repr__(self):
		return '(PClass %s)' % ', '.join(
			['%s = %r' % (k, getattr(self, k))
				for k in self.fields if hasattr(self, k)])
