# -*- coding: utf-8 -*-
''' Klarna API - checkout - checkout loader

Provides a method for dynamicly loading checkout extensions
'''

#
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

__all__ = ('get_checkout_classes',)

import logging
from .checkouthtml import CheckoutHTML

logger = logging.getLogger('klarna')


def get_checkout_classes():
	''' Finds all checkout classes '''

	import os
	import sys
	import imp
	import glob

	classes = []
	modules = ['__init__']

	base = os.path.dirname(__file__)

	for (suffix, mode, t) in imp.get_suffixes():
		for f in glob.glob(os.path.join(base, '*%s' % suffix)):
			name = os.path.basename(f)[:-len(suffix)]
			if name in modules:
				continue
			fullname = '%s.%s' % (__name__, name)
			fp, pathname, description = imp.find_module(name, [base])

			try:
				module = sys.modules[fullname]
				logger.debug('Checkout HTML module (%s) already loaded' % name)
			except:
				# Try to import the module
				(fp, pathname, description) = imp.find_module(name, [base])
				logger.debug('Loading Checkout HTML module from %s' % pathname)
				try:
					module = imp.load_module(fullname, fp, pathname, description)
				finally:
					if fp:
						fp.close()
			modules.append(name)

			# Find all CheckoutHTML subclasses
			for export in dir(module):
				o = getattr(module, export)
				try:
					if o is not CheckoutHTML and issubclass(o, CheckoutHTML):
						classes.append(o)
				except TypeError:
					# not a class
					pass

	return classes
