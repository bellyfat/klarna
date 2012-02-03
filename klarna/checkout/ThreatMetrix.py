''' Klarna API - checkout - ThreatMetrix

Threatmetrix integration
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

from .checkouthtml import CheckoutHTML

template = '<p style="display: none; background:url(%(scheme)s://%(host)s/fp/'\
	'clear.png?org_id=%(orgid)s&amp;session_id=%(sid)s&amp;m=1);"></p>'\
	'<script src="%(scheme)s://%(host)s/fp/check.js?org_id=%(orgid)s&amp;'\
	'session_id=%(sid)s" type="text/javascript"></script>'\
	'<img src="%(scheme)s://%(host)s/fp/clear.png?org_id=%(orgid)s&amp;'\
	'session_id=%(sid)s&amp;m=2\" alt="" />'\
	'<object type="application/x-shockwave-flash" style="display: none" data='\
	'"%(scheme)s://%(host)s/fp/fp.swf?org_id=%(orgid)s&amp;session_id=%(sid)s" '\
	'width="1" height="1" id="obj_id">'\
	'<param name="movie" value="%(scheme)s://%(host)s/fp/fp.swf?org_id=%(orgid)s'\
	'&amp;session_id=%(sid)s" /><div></div></object>'


class ThreatMetrix(CheckoutHTML):
	# The ID used in conjunction with the Klarna API
	ID = 'dev_id_1'

	# ThreatMetrix organizational ID
	orgID = 'qicrzsu4'

	# Hostname used to access ThreatMetrix
	host = 'h.online-metrix.net'

	# Protocol used to access ThreatMetrix
	scheme = 'https'

	def __init__(self, klarna, eid, session=None):
		''' Initialises ThreatMetrix integration
			session should be a dictionary-like object where session variables
			can be read and saved (e.g beaker session or pythonweb session)
		'''

		if session is None:
			self.session_id = self.get_session_id(eid)
		else:
			if self.ID not in session or len(session[self.ID]) < 40:
				session[self.ID] = self.session_id = self.get_session_id(eid)
			else:
				self.session_id = session[self.ID]

		klarna.set_session_id(self.ID, self.session_id)

	def clear(self, session):
		''' Clears the ThreatMetrix session variable from the given
			dictionary-like session object
		'''

		session[self.ID] = None
		try:
			del session[self.ID]
		except:
			pass

	def to_html(self):
		info = {'scheme': self.scheme,
			'host': self.host,
			'orgid': self.orgID,
			'sid': self.session_id}

		return template % info
