#!/usr/bin/env python
"""
	Pazookle Audio Programming Language
	Copyright (C) 2013 Bob Harris.  All rights reserved.

    This file is part of Pazookle.

	Pazookle is free software: you can redistribute it and/or modify it under
	the terms of the GNU General Public License as published by the Free
	Software Foundation, either version 3 of the License, or (at your option)
	any later version.

	This program is distributed in the hope that it will be useful, but WITHOUT
	ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
	FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
	more details.

	You should have received a copy of the GNU General Public License along
	with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
__version__   = "0.01"
__author__    = "Bob Harris (zackobelsch@gmail.com)"
__copyright__ = "(C) 2013 Bob Harris. GNU GPLv3."

from math import exp,cos
from ugen import UGenError


def piecewise(splits,funcs):
	"""Create an interpolation function by piecing together several functions.

	splits is a list of x values (sorted by non-decreasing x)
	funcs  is a list of interpolation functions to piece together

	funcs[0] is applied for              x < splits[0]
	funcs[1] is applied for splits[0] <= x < splits[1]
	 ...
	funcs[n] is applied for x > splits[n-1]
	"""
	numFuncs = len(funcs)
	if (len(splits) != numFuncs-1):
		msg = "(in piecewise) %s splits requires %s functions (%s functions provided)" \
		    % (len(splits),numFuncs)
		raise UGenError(msg)
	if (numFuncs == 1): return funcs[0]
	# make sure splits are non-decreasing
	for ix in xrange(1,numFuncs-1):
		if (splits[ix-1] > splits[ix]):
			msg = "(in piecewise) splits are not in non-decreasing order [%s]" \
			    % ",".join([str(s) for x in splits])
			raise UGenError(msg)
	# build function over sorted segments
	return _piecewise(splits,funcs)


def _piecewise(splits,funcs):
	# partition segments into functions covering left and right halves
	numFuncs = len(funcs)
	assert (numFuncs >= 2), \
	       "internal error: _piecewise wasn't given enough functions (given %s)" \
	     % numFuncs
	midIx    = (numFuncs-2) / 2
	xMid     = splits[midIx]
	if (midIx == 0):          fLeft  = funcs[0]
	else:                     fLeft  = _piecewise(splits[:midIx],funcs[:midIx+1])
	if (midIx == numFuncs-2): fRight = funcs[numFuncs-1]
	else:                     fRight = _piecewise(splits[midIx+1:],funcs[midIx+1:])
	# build function by combining left and right halves
	return lambda x: fLeft(x) if (x < xMid) else fRight(x)


def linear_ramp(x1,x2,y1,y2):
	"""Create a linear interpolation function.

	Create a linear polynomial f(x) which when evaluated over the range x1..x2
	ranges from y1 to y2.
	"""
	if (x1 == x2):
		msg = "(in linear_ramp) x1=%s and x2=%s cannot be equal" % (x1,x2)
		raise UGenError(msg)
	(x1,x2,y1,y2) = (float(x1),float(x2),float(y1),float(y2))
	return lambda x: y1 + (y2-y1)*(x-x1)/(x2-x1)


def diminishing_exponential(x1,x2,y1,y2,speed=5.0,epsilon=1e-6):
	"""Create a exponential interpolation function.

	Create a linear polynomial f(x) which when evaluated over the range x1..x2
	ranges from y1 to y2, with a decreasing rate of change.
	"""
	if (x1 == x2):
		msg = "(in diminishing_exponential) x1=%s and x2=%s cannot be equal" % (x1,x2)
		raise UGenError(msg)
	(x1,x2,y1,y2) = (float(x1),float(x2),float(y1),float(y2))
	u = y2 + (y2-y1) * epsilon
	v = (y1-y2) * (1+epsilon)
	w = speed / (x1-x2)
	return lambda x: u + v * exp(w*(x-x1))


def sinusoidal_ess(x1,x2,y1,y2):
	"""Create an S-shaped interpolation function.

	Create a function f(x) consisting of one half cycle of a cosine wave, which
	when evaluated over the range x1..x2 ranges smoothly from y1 to y2 and is
	flat (horizontal) at both ends.
	"""
	if (x1 == x2):
		msg = "(in sinusoidal_ess) x1=%s and x2=%s cannot be equal" % (x1,x2)
		raise UGenError(msg)
	(x1,x2,y1,y2) = (float(x1),float(x2),float(y1),float(y2))
	xScale = pi/(x2-x1)
	yScale = (y1-y2)/2.0
	yBias  = (y1+y2)/2.0
	return lambda x: yBias + yScale*cos(xScale*(x-x1))


def cubic_ess(x1,x2,y1,y2):
	"""Create an S-shaped interpolation function.

	Create a cubic polynomial f(x) which when evaluated over the range x1..x2
	ranges smoothly from y1 to y2 and is flat (horizontal) at both ends.
	"""
	if (x1 == x2):
		msg = "(in cubic_ess) x1=%s and x2=%s cannot be equal" % (x1,x2)
		raise UGenError(msg)
	(x1,x2,y1,y2) = (float(x1),float(x2),float(y1),float(y2))
	denom = (x2-x1) * (x2-x1) * (x2-x1)
	a     = (2*(y1-y2)                                                ) / denom
	b     = (3*(x2+x1)*(y2-y1)                                        ) / denom
	c     = (6*x1*x2*(y1-y2)                                          ) / denom
	d     = (x2*x2*x2*y1 - 3*x2*x2*y1*x1 + 3*x2*y2*x1*x1 - y2*x1*x1*x1) / denom
	return lambda x: a*x*x*x + b*x*x + c*x + d


