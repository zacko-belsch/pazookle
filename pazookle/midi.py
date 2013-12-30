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

from math import exp


semitone   = 1.0594630943592952646  # 12th root of 2
lnSemitone = 0.0577622650466621091  # log base e of 12th root of 2
lnOctave   = 0.6931471805599453094  # log base e of 2


def midi_to_freq(midiNote):
	"""Convert a midi note number to the corresponding frequency.

	midiNote is usally an integer in the range 0..127, but can be a float and
	can be outside that range.
	"""
	# midiNote m=69 corresponds to frequency 440, so if s is the semitone
	# ratio (12th root of 2), we have
	# f = 440 * s^(m-69)
	# => ln f = ln 440 + (m-69)ln s
	# => ln f = m*ln s + (ln 440 - 69ln s)
	k = 2.1011784386926213178  # (ln 440 - 69ln s)
	f = exp(midiNote*lnSemitone + k)
	return f


def build_scale(mode,root,numNotes=None):
	"""Create a list of midi note numbers for a given scale/mode.

	mode is one of the musical scale modes, such as "ionian", "dorian" and
	so on.

	midiNote is usally an integer in the range 0..127, but can be a float.  It
	cannot be negative.

	numNotes is usally the number of notes in the created list.  It can also
	be a (minNote,maxNote) pair, in which case we'll append unused entries to
	the front of the list.

	The caller can call this with two arguments instead of three, in which
	case we automtically insert "ionian" as the first argument.
	"""

	if (numNotes == None):
		(mode,root,numNotes) = ("ionian",mode,root)

	if (root < 0):
		msg = "\"%s\" is not an allowed root for build_scale" % root
		raise ValueError(msg)

	rootWhole = int(root)
	rootFrac  = root - rootWhole

	if (type(numNotes) == int): (minNote,maxNote) = (0,numNotes-1)
	else:                       (minNote,maxNote) = numNotes

	lowMode = mode.lower()
	if   (lowMode == "i"):   lowMode = "ionian"
	elif (lowMode == "ii"):  lowMode = "dorian"
	elif (lowMode == "iii"): lowMode = "phrygian"
	elif (lowMode == "iv"):  lowMode = "lydian"
	elif (lowMode == "v"):   lowMode = "mixolydian"
	elif (lowMode == "vi"):  lowMode = "aeolian"
	elif (lowMode == "vii"): lowMode = "locrian"

	if   (lowMode == "ionian"):     magic = 7*rootWhole+5
	elif (lowMode == "dorian"):     magic = 7*rootWhole+3
	elif (lowMode == "phrygian"):   magic = 7*rootWhole+1
	elif (lowMode == "lydian"):     magic = 7*rootWhole+6
	elif (lowMode == "mixolydian"): magic = 7*rootWhole+4
	elif (lowMode == "aeolian"):    magic = 7*rootWhole+2
	elif (lowMode == "locrian"):    magic = 7*rootWhole
	else:
		msg = "\"%s\" is not recognized mode for build_scale" % mode
		raise ValueError(msg)

	scale = [None] * (maxNote+1)
	for degree in xrange(minNote,maxNote+1):
		scale[degree] = (12*degree+magic)/7 + rootFrac

	return scale


def build_pentatonic_scale(mode,root,numNotes=None):
	"""Create a list of midi note numbers for a given pentatonic scale/mode.

	mode is one of five musical scale modes, identified as roman numerals.

	midiNote is usally an integer in the range 0..127, but can be a float.  It
	cannot be negative.

	numNotes is usally the number of notes in the created list.  It can also
	be a (minNote,maxNote) pair, in which case we'll append unused entries to
	the front of the list.

	The caller can call this with two arguments instead of three, in which
	case we automtically insert "i" as the first argument.
	"""

	if (numNotes == None):
		(mode,root,numNotes) = ("i",mode,root)

	if (root < 0):
		msg = "\"%s\" is not an allowed root for midi_pentatonic" % root
		raise ValueError(msg)

	rootWhole = int(root)
	rootFrac  = root - rootWhole

	if (type(numNotes) == int): (minNote,maxNote) = (0,numNotes-1)
	else:                       (minNote,maxNote) = numNotes

	lowMode = mode.lower()
	if   (lowMode == "i"):   magic = 5*rootWhole+3
	elif (lowMode == "ii"):  magic = 5*rootWhole+1
	elif (lowMode == "iii"): magic = 5*rootWhole+4
	elif (lowMode == "iv"):  magic = 5*rootWhole+2
	elif (lowMode == "v"):   magic = 5*rootWhole+0
	else:
		msg = "\"%s\" is not recognized mode for midi_pentatonic" % mode
		raise ValueError(msg)

	scale = [None] * (maxNote+1)
	for degree in xrange(minNote,maxNote+1):
		scale[degree] = (12*degree+magic)/5 + rootFrac

	return scale
