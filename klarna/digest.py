''' Klarna API - Digest

helper for digest calculation done by candice and core api
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

__all__ = ('get_digest',)

import sys
import hashlib
from base64 import b64encode


# Find a good hash algorithm
for m in ('sha512', 'sha256', 'md5'):
	try:
		default_method = getattr(hashlib, m)
		break
	except AttributeError:
		pass
else:
	raise Exception('Found no suitable hash algorithm')


# DEPRECATED
def md5b64(s):
	''' Returns the md5 hash of s as a base64 encoded string (deprecated) '''
	return get_digest(s, hashlib.md5)


def get_digest(s, method=default_method):
	if sys.version_info >= (3,):
		s = s.encode('iso8859-1')
	else:
		if isinstance(s, unicode):
			s = s.encode('iso8859-1')
	return b64encode(method(s).digest()).decode('ascii')
