#!/usr/bin/env python

import os
from setuptools import setup


def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
	name="klarna",
	version="2.1.1",
	author="David Keijser",
	description=("The Klarna API used to communicate with Klarna Online"),
	license="BSD",
	keywords="klarna xmlrpc payment",
	url="http://integration.klarna.com",
	packages=['klarna', 'klarna.checkout', 'klarna.pclasses'],
	long_description=read('README'),
	classifiers=[
		"Development Status :: 4 - Beta",
		"Topic :: Office/Business",
		"License :: OSI Approved :: BSD License",
	],
)
