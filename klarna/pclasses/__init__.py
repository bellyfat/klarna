# -*- coding: utf-8 -*-
''' Klarna API - pclasses - storage loader

Provides a method for dynamicly loading pclass storages
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

__all__ = ('get_pclass_storage',)

import logging
from .storage import PCStorage
from ..error import KlarnaException

logger = logging.getLogger('klarna')


def get_pclass_storage(name):
	''' Finds and loads a PClass storage backend by name '''

	logger.info('Using PClass storage module %s' % name)

	# A non empty fromlist makes import return the deepest module as it
	# assumes we are going to import some names directly
	try:
		module = __import__('klarna.pclasses.' + name + 'storage', fromlist=[''])
	except ImportError:
		module = __import__(name, fromlist=[''])

	# Find the first PCStorage subclass and instanciate it
	for export in dir(module):
		o = getattr(module, export)
		if isinstance(o, type) and issubclass(o, PCStorage):
			return o()

	raise KlarnaException("No PCStorage subclass found in %r" % module)
