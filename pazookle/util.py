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

def raise_to_mulitple(val,multipleOf):
	return multipleOf * ((val + multipleOf-1) / multipleOf)


def clip_value(sample,sampleMin,sampleMax=None):
	"""Clip an value within a specified range.

	If sampleMax is not provided, the absolute value of sampleMin is used as
	the max, and the negative of that is used as the min.
	"""
	if (sampleMax == None):
		sampleMax = abs(sampleMin)
		sampleMin = -sampleMax
	if (sample <= sampleMin): return sampleMin
	if (sample >= sampleMax): return sampleMax
	return sample

