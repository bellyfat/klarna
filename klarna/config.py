# -*- coding: utf-8 -*-
''' Klarna API - Config

Defines a Config class that load and saves configuration as json
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

# python3k campatibility
from __future__ import print_function
import sys
if sys.version_info >= (3,):
	basestring = str

__all__ = ('Config',)

import json
import logging

logger = logging.getLogger('klarna')


class Config(dict):
	''' Configuration holder for the Klarna instance.

		backed by json on file if Config.store is set to True
	'''

	store = True

	def __init__(self, file=None, **kwargs):
		''' if a single argument is given it's used as the filename to load
			the configuration from. Else the config is populated from the keyword
			arguments
		'''

		self.file = file

		# Load the file if any
		try:
			if self.file is not None:
				with open(self.file) as fp:
					self.update(json.load(fp))
		except:
			logger.warn('Could not load config', exc_info=True)

		# Fill the config with values from keyword arguments
		self.update(kwargs)

	def __del__(self):
		try:
			if self.store and self.file is not None:
				self.save()
		except IOError:
			logger.warn('Could not save config', exc_info=True)

	def save(self):
		string = json.JSONEncoder().encode(self)
		with open(self.file, 'w') as fp:
			fp.write(string)
