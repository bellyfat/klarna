''' Klarna API - checkout - checkouthtml

baseclass for checkout extensions
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

from ..error import KlarnaException


class CheckoutHTML(object):
	def get_session_id(self, eid):
		''' Creates a session used for e.g client identification and fraud
			prevention.

			The returned string consist of 40 characters 0-9 computed as follows:
			* the first 30 is time padded with random numbers
			* the last 10 is the eid zero-padded
		'''

		import time
		import random

		eid = '%010d' % eid
		sid = str(time.time()).replace('.', '')
		# Get random int between minumum and maximum int represented
		# with remaining chars
		min = 10 ** (30 - len(sid) - 1)
		max = 10 ** (30 - len(sid)) - 1
		rand = str(random.randint(min, max))

		return '%s%s%s' % (sid, rand, eid)

	def to_html(self, uri):
		raise KlarnaException("to_html not implemented by CheckoutHTML subclass")

	def clear(self, uri):
		raise KlarnaException("clear not implemented by CheckoutHTML subclass")
