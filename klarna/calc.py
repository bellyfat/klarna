''' Klarna API - Calc

All rates are yearly rates, but they are calculated monthly. So
a rate of 9 % is used 0.75% monthly. The first is the one we specify
to the customers, and the second one is the one added each month to
the account. The IRR uses the same notation.

The APR is however calculated by taking the monthly rate and raising
it to the 12 power. This is according to the EU law, and will give
very large numbers if the $pval is small compared to the $fee and
the amount of months you repay is small as well.

All functions work in discrete mode, and the time interval is the
mythical evenly divided month. There is no way to calculate APR in
days without using integrals and other hairy math. So don't try.
The amount of days between actual purchase and the first bill can
of course vary between 28 and 61 days, but all calculations in this
class assume this time is exactly and that is ok since this will only
overestimate the APR and all examples in EU law uses whole months as well.
Provides Address class which holds a single address of a person or company
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

__all__ = ('calc_apr',
	'total_credit_purchase_cost',
	'calc_monthly_cost',
	'get_lowest_payment_for_account',
	'pround')

from math import log, ceil
from .error import KlarnaException
from .const import Page
from .pclass import PClass

accuracy = 0.01


def midpoint(a, b):
	return (a + b) / 2


def npv(pval, payarray, rate, fromdayone):
	''' npv - Net Present Value
	'''

	for i, payment in enumerate(payarray):
		pval -= payment / pow(1 + rate / (12 * 100.0), fromdayone + i)

	return pval


def irr(pval, payarray, fromdayone):
	''' irr - Internal Rate of Return
		This function uses divide and conquer to numerically find the IRR
	'''

	low = 0.0
	high = 100.0
	lowval = npv(pval, payarray, low, fromdayone)
	highval = npv(pval, payarray, high, fromdayone)

	if lowval > 0.0:
		return -1  # raise Exception ?

	while high < 1000000:
		mid = midpoint(low, high)
		midval = npv(pval, payarray, mid, fromdayone)
		if abs(midval) < accuracy:
			# Close enough
			return mid

		if highval < 0:
			# not in range, double it
			low, lowval = high, highval
			high *= 2
			highval = npv(pval, payarray, high, fromdayone)
		elif midval >= 0:
			# irr is between low and mid
			high, highval = mid, midval
		else:
			# irr is between mid and high
			low, lowval = mid, midval

	return -2


def irr2apr(irr):
	''' Turns IRR into APR

		IRR is not the same thing as APR, Annual Percentage Rate. The
		IRR is per time period, i.e. 1 month, and the APR is per year,
		and note that that you need to raise to the power of 12, not
		mutliply by 12.
	'''
	return (100 * (pow(1 + irr / (12 * 100.0), 12) - 1))


def fulpacc(pval, rate, fee, minpay, payment, months, base):
	''' This is a simplified model of how our paccengine works if
		a client always pays their bills. It adds interest and fees
		and checks minimum payments. It will run until the value
		of the account reaches 0, and return an array of all the
		individual payments. Months is the amount of months to run
		the simulation. Important! Don't feed it too few months or
		the whole loan won't be paid off, but the other functions
		should handle this correctly.

		Giving it too many months has no bad effects, or negative
		amount of months which means run forever, but it will stop
		as soon as the account is paid in full.

		Depending if the account is a base account or not, the
		Payment has to be 1/24 of the capital amount.

		The payment has to be at least $minpay, unless the capital
		amount + interest + fee is less than $minpay; in that case
		that amount is paid and the function returns since the client
		no longer owes any money.
	'''

	bal = pval
	payarray = []
	while months != 0 and bal > accuracy:
		interest = bal * rate / (100.0 * 12)
		nbal = bal + interest + fee

		if minpay >= nbal or payment >= nbal:
			payarray.append(nbal)
			return payarray

		npay = max(payment, minpay)
		if base:
			npay = max(npay, bal / 24.0 + fee + interest)

		bal = nbal - npay
		payarray.append(npay)
		months -= 1

	return payarray


def annuity(pval, months, rate):
	''' Calculates how much you have to pay each month if you want to
		pay exactly the same amount each month. The interesting input
		is the amount of $months.

		It does not include the fee so add that later.
	'''

	if months == 0:
		return pval

	if round(rate, 0) == 0:
		return pval / months
	p = rate / (100.0 * 12)
	return pval * p / (1 - pow(1 + p, -months))


def fixed(pval, monthly, rate, fromdayone):
	''' How many months does it take to pay off a loan if I pay
		exactly monthly each month? It might actually go faster
		if you hit the minimum payments, but this function returns
		the longest amount of months.

		This function _does_ not include the fee, so remove the fee
		from the monthly before sending it into this function.

		Returns values: float months
						int   -1		you are not paying more than
										the interest. infinity
						int   -2		fromdayone has to be 0 or 1
	'''

	p = rate / (100 * 12)
	f = 1 + p

	if fromdayone == 0:
		if f < pval * p / monthly:
			return -1
		return 1 - log(f - pval * p / monthly) / log(f)
	elif fromdayone == 1:
		if 1.0 < pval * p / monthly:
			return -1
		return -log(1.0 - pval * p / monthly) / log(f)
	else:
		return -2


def apr_annuity(pval, months, rate, fee, minpay):
	''' Calculate the APR for an annuity '''

	payment = annuity(pval, months, rate) + fee
	if payment < 0:
		return payment

	payarray = fulpacc(pval, rate, fee, minpay, payment, months, False)
	apr = irr2apr(irr(pval, payarray, 1))

	return apr


def apr_fixed(pval, payment, rate, fee, minpay):
	''' Calculate the APR given a fixed payment each month. '''

	months = fixed(pval, payment - fee, rate, 1)
	if months < 0:
		return months

	months = ceil(months)
	payarray = fulpacc(pval, rate, fee, minpay, payment, months, False)
	apr = irr2apr(irr(pval, payarray, 1))

	return apr


def apr_min(pval, rate, fee, minpay):
	''' This tries to pay the absolute minimum each month.
		Give the absolute worst APR.
		Don't export, only here for reference.
	'''

	payarray = fulpacc(pval, rate, fee, minpay, 0.0, -1, True)
	apr = irr2apr(irr(pval, payarray, 1))

	return apr


def apr_payin_X_months(pval, payment, rate, fee, minpay, free):
	''' Calculates APR for a campaign where you give $free months to
		the client and there is no interest on the first invoice.
		The only new input is $free, and if you give "Pay in Jan"
		in November, then $free = 2.
	'''

	firstpay = payment
	months = fixed(pval, payment - fee, rate, 0)
	if months < 0:
		return months

	months = ceil(months)
	farray = [0.0 for f in range(free)]
	pval += fee

	farray.append(firstpay)
	pval -= firstpay

	payarray = fulpacc(pval, rate, fee, minpay, payment, months, False)
	farray.extend(payarray)
	apr = irr2apr(irr(pval, farray, 1))

	return apr


def get_payarr(tot, pclass, page):
	''' Grabs the array of all monthly payments for specified PClass.
	'''

	if page is Page.CHECKOUT:
		monthsfee = pclass.invoicefee
		startfee = pclass.startfee
	else:
		monthsfee = 0
		startfee = 0

	# Include start fee in sum
	tot += startfee

	if pclass.type == PClass.Type.ACCOUNT:
		base = True
	else:
		base = False

	lowest = get_lowest_payment_for_account(pclass.country)
	if page is Page.CHECKOUT:
		minpay = lowest
	else:
		minpay = 0

	payment = annuity(tot, pclass.months, pclass.interestrate)
	payment += monthsfee

	return fulpacc(tot, pclass.interestrate, monthsfee, minpay, payment,
		pclass.months, base)


def calc_apr(tot, pclass, page, free=0):
	''' Calculates APR for the specified values.
	'''

	tot = float(tot)

	if free < 0:
		raise KlarnaException("Number of free months must be positive or zero")

	if page is Page.CHECKOUT:
		monthsfee = pclass.invoicefee
		startfee = pclass.startfee
	else:
		monthsfee = 0
		startfee = 0

	# Include start fee in sum
	tot += startfee

	lowest = get_lowest_payment_for_account(pclass.country)
	if page is Page.CHECKOUT and pclass.type == PClass.Type.ACCOUNT:
		minpay = lowest
	else:
		minpay = 0

	payment = annuity(tot, pclass.months, pclass.interestrate) + monthsfee
	if pclass.type in (PClass.Type.CAMPAIGN, PClass.Type.ACCOUNT):
		apr = apr_annuity(tot, pclass.months, pclass.interestrate, pclass.invoicefee,
			minpay)
	elif pclass.type == PClass.Type.SPECIAL:
		apr = apr_payin_X_months(tot, payment, pclass.interestrate,
			pclass.invoicefee, minpay, free)
	elif pclass.type == PClass.Type.FIXED:
		apr = apr_fixed(tot, payment, pclass.interestrate, pclass.invoicefee, minpay)
	else:
		raise KlarnaException("Unknown PClass type %r" % pclass.type)

	return round(apr, 2)


def total_credit_purchase_cost(tot, pclass, page):
	''' Calculates the total credit purchase cost.
	'''

	tot = float(tot)

	if page is Page.CHECKOUT:
		startfee = pclass.startfee
	else:
		startfee = 0

	payarray = get_payarr(tot, pclass, page)

	credit_cost = sum(payarray)
	return credit_cost + startfee


def calc_monthly_cost(tot, pclass, page):
	''' Calculates the monthly cost for the specified pclass.
		The result is rounded up to the correct value depending on the pclasses
		country.
	'''

	payarray = get_payarr(tot, pclass, page)

	if len(payarray) > 0:
		val = payarray[0]
	else:
		val = 0

	if page is Page.CHECKOUT:
		return round(val, 2)

	return pround(val, pclass.country)


def get_lowest_payment_for_account(country):
	''' Returns the lowest monthly payment for Klarna Account.
	'''

	lpby = {
		'SE': 50.0,
		'NO': 95.0,
		'FI': 8.95,
		'DK': 89.0,
		'DE': 6.95,
		'NL': 6.95}

	return lpby[country]


def pround(value, country):
	if country in ('DE', 'NL'):
		return round(value, 1)
	return round(value, 0)
