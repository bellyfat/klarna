''' Klarna API - Candice

Statistics reporting
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

__all__ = ('Candice',)

import socket
import logging
from .digest import md5b64

logger = logging.getLogger('klarna')


class Candice(object):
	def __init__(self, address, port, eid, secret, url):
		self.__address = address
		self.__port = port
		self.__eid = eid
		self.__secret = secret
		self.__url = url

	def send_stat(self, method, time, select_time, status):
		vals = [str(self.__eid), method, str(time), str(select_time), str(status),
			self.__url]
		digest = md5b64('|'.join(vals + [self.__secret]))
		data = '|'.join(vals + [digest])

		logger.debug('candice %r', data)

		# Open connection to candice
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		except IOError:
			logger.warning("could not open candice socket", exc_info=True)

		# Send stats
		try:
			sock.sendto(data, (self.__address, self.__port))
		except:
			logger.warning('error sending candice report', exc_info=True)
		finally:
			sock.close()
