# -*- coding: utf-8 -*-
''' Klarna API - pclasses - JSON Storage

Defines the PCStorage implementation storing pclasses using JSON
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

__all__ = ('JSONStorage',)

from .storage import PCStorage, PClass
from ..error import KlarnaException
import os
import json


class JSONStorage(PCStorage):
	''' Stores PClasses in json
		this class works with the same structure as the php-api
	'''

	def load(self, uri):
		with open(uri, 'r') as fp:
			data = json.load(fp)

		# add pclasses from json-data
		for eid, pclasses in data.items():
			for pclass in pclasses:
				pclass = PClass(**pclass)
				self.add_pclass(pclass)

	def save(self, uri):
		if not hasattr(self, '_pclasses'):
			raise KlarnaException('No PClasses found')

		# Convert pclass database to a structure that json can dump
		output = {}
		for eid, pclasses in self._pclasses.items():
			for pclass in pclasses.values():
				if eid not in output:
					output[eid] = []
				output[eid].append(dict(list(pclass)))

		string = json.JSONEncoder().encode(output)
		with open(uri, 'w') as fp:
			fp.write(string)

	def clear(self, uri):
		if hasattr(self, '_pclasses'):
			del self._pclasses
		if os.path.exists(uri):
			os.unlink(uri)
