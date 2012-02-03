# -*- coding: utf-8 -*-
''' Klarna API - pclasses - Storage

Defines the shared interface of all PClass storages
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

__all__ = ('PCStorage',)

import logging

from ..error import KlarnaException
from ..pclass import PClass

logger = logging.getLogger('klarna')


class PCStorage(object):
	def add_pclass(self, pclass):
		if not isinstance(pclass, PClass):
			raise TypeError("Supplied pclass object is not an PClass instance")

		if not hasattr(self, '_pclasses'):
			self._pclasses = {}

		# Sanity checks
		if getattr(pclass, 'description', None) is None:
			logger.warning("Missing description on PClass, skipping")
			return
		if getattr(pclass, 'type', None) is None:
			logger.warning("Missing type on PClass, skipping")
			return

		if pclass.eid not in self._pclasses:
			self._pclasses[pclass.eid] = {}
		logger.debug("Adding pclass %s", pclass)
		self._pclasses[pclass.eid][pclass.id] = pclass

	def get_pclass(self, id, eid):
		''' Get PClass by id and eid '''

		if not hasattr(self, '_pclasses'):
			raise KlarnaException('No PClasses found')

		try:
			pclass = self._pclasses[eid][id]
		except KeyError:
			if eid not in self._pclasses:
				raise KlarnaException("No such EStore ID (%s)" % eid)
			raise KlarnaException("Nu such PClass ID (%s)" % id)

		if not pclass.is_valid():
			raise KlarnaException("Invalid PClass")

		return pclass

	def get_pclasses(self, country, type=None):
		''' Get dictionaries with PClass instances mapped to eid and pclass id
			filtered by by country and type (if specified)
		'''

		if not hasattr(self, '_pclasses'):
			raise KlarnaException('No PClasses found')

		country = country.upper()
		out = {}
		for eid, pclasses in self._pclasses.items():
			for pid, pclass in pclasses.items():
				if not pclass.is_valid():
					continue

				if type is not None and pclass.type != type:
					continue

				if pclass.country != country:
					continue

				if eid not in out:
					out[eid] = {}
				out[eid][pclass.id] = pclass
		return out

	def load(self, uri):
		raise KlarnaException("load not implemented by PCStorage subclass")

	def save(self, uri):
		raise KlarnaException("save not implemented by PCStorage subclass")

	def clear(self, uri):
		raise KlarnaException("clear not implemented by PCStorage subclass")
