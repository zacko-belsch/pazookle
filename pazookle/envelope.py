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

from ugen        import UGen
from interpolate import piecewise,linear_ramp,diminishing_exponential, \
                        sinusoidal_ess,cubic_ess


class Impulse(UGen):
	"""A single impulse object, changing to a given target value for one sample.

	If this ugen has any feeds, the feed(s) is multiplied by the ugen's value
	(the target value or zero).  Otherwise, the ugen's value is output.
	"""

	def __init__(self,channels=1,inChannels=None,name=None,
	             bias=0.0,gain=1.0):
		super(Impulse,self).__init__(inChannels=inChannels if (inChannels!=None) else channels,
		                             outChannels=channels,name=name,
		                             bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "Impulse.__init__(%s)" % name
		if (self.inChannels != 0) and (self.inChannels != self.outChannels):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		self._defaultInSample = 1.0
		self._target          = 0.0

	def trigger(self,target):
		self._target = target

	def tick(self,sample=None,sample2=None):
		target = self._target
		self._target = 0.0
		if (sample  == None): sample = self._defaultInSample
		if (sample2 == None): return (target*sample)
		else:                 return (target*sample,target*sample2)


class Step(UGen):
	"""A simple step object, immediately changing to a given target value.

	This class also serves as a parent class for all triggered steps.

	If this ugen has any feeds, the feed(s) is multiplied by the ugen's value
	(the target value or the transition to it).  Otherwise, the ugen's value is
	output.
	"""

	def __init__(self,channels=1,inChannels=None,name=None,
	             bias=0.0,gain=1.0):
		super(Step,self).__init__(inChannels=inChannels if (inChannels!=None) else channels,
		                          outChannels=channels,name=name,
		                          bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "Step.__init__(%s)" % name
		if (self.inChannels != 0) and (self.inChannels != self.outChannels):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		self._defaultInSample = 1.0
		self._active          = False
		self._current         = 0.0
		self._target          = 0.0

	def trigger(self,target,duration=None):
		self._current = self._target = target

	def tick(self,sample=None,sample2=None):
		if (sample  == None): sample = self._defaultInSample
		if (sample2 == None): return (self._target*sample)
		else:                 return (self._target*sample,self._target*sample2)


class LinearRamp(Step):
	"""Ramp linearly to a given target value.

	This class also serves as a parent class for all ramp-to steps.
	"""

	def trigger(self,target,duration,makeInterpolator=True):
		self._startTime = UGen.shreduler.now()
		self._endTime   = UGen.shreduler.now() + duration
		self._deltaTime = duration
		self._startVal  = self._current
		self._target    = target
		self._active    = True
		if (makeInterpolator):
			self._interpolator = lambda x: (self._target-self._startVal) * x
		if ("Step" in UGen.debug):
			print >>stderr, "LinearRamp.trigger(%s)" % self
			print >>stderr, "  deltaTime = %s" % self._deltaTime
			print >>stderr, "  startTime = %s" % self._startTime
			print >>stderr, "  endTime   = %s" % self._endTime
			print >>stderr, "  startVal  = %s" % self._startVal
			print >>stderr, "  target    = %s" % self._target
			print >>stderr, "  active    = %s" % self._active

	def tick(self,sample=None,sample2=None):
		if (not self._active):
			val = self._target
		elif (UGen.shreduler.clock() < self._endTime):
			x = (UGen.shreduler.clock() - self._startTime) / self._deltaTime
			val = self._startVal + self._interpolator(x)
		else:
			self._active = False
			val = self._target

		self._current = val
		if ("envelopes" in UGen.debug):
			print >>stderr, "%s %d %s" % (self,UGen.shreduler.clock(),val)

		if (sample  == None): sample = self._defaultInSample
		if (sample2 == None): return (val*sample)
		else:                 return (val*sample,val*sample2)


class CubicRamp(LinearRamp):
	"""Ramp to a given target value with a smooth "S" function."""

	def trigger(self,targetVal,duration,makeInterpolator=True):
		super(CubicRamp,self).trigger(targetVal,duration,makeInterpolator=False)
		if (makeInterpolator):
			self._interpolator = cubic_ess(0.0,1.0,0.0,self._target-self._startVal)


class Envelope(LinearRamp):
	"""Parent class for envelopes

	As with step ugens, if this ugen has any feeds, the feed(s) is multiplied
	by the envelope's value.  Otherwise, the envelope's value is output.
	"""

	def __init__(self,channels=1,inChannels=None,name=None,
	             bias=0.0,gain=1.0,
	             ar=None,attack=None,release=None):
		super(Envelope,self).__init__(channels=channels,inChannels=inChannels,name=name,
		                              bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "Envelope.__init__(%s)" % name

		if (ar != None): (attack,release) = ar
		self.set(attack=attack,release=release)
		self._defaultInSample = 1.0
		self._active          = False
		self._target          = 0.0

	def set(self,attack,release):
		if   (attack  == None): attack  = UGen.defaultAttack
		elif (attack  <  1):    attack  = 1
		if   (release == None): release = UGen.defaultRelease
		elif (release <  1):    release = 1
		self._attack   = attack
		self._release  = release

	def key_on(self,velocity=None,makeInterpolator=True):
		if (velocity == None): velocity = 1.0
		self.trigger(velocity,self._attack,makeInterpolator=False)
		self._interpolator = lambda x: (self._target-self._startVal) * x

	def key_off(self,makeInterpolator=True):
		self.trigger(0.0,self._release,makeInterpolator=False)
		self._interpolator = lambda x: (self._target-self._startVal) * x

	#-- non-drivable attack, with side effects --

	@property
	def attack(self):
		return self._attack

	@attack.setter
	def attack(self,attack):
		self.set(attack,self.release)

	#-- non-drivable release, with side effects --

	@property
	def release(self):
		return self._release

	@release.setter
	def release(self,release):
		self.set(self.attack,release)


class ADSR(LinearRamp):
	"""Attack-decay-sustain-release envelopes"""
	# $$$ need to make each piece of the envelope be specifiable as "linear"
	#     .. or "exponential up" or "exponential down", also true for Envelope

	def __init__(self,channels=1,inChannels=None,name=None,
	             bias=0.0,gain=1.0,
	             adsr=None,attack=None,decay=None,sustain=None,release=None):
		super(ADSR,self).__init__(channels=channels,inChannels=inChannels,name=name,
		                          bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "ADSR.__init__(%s)" % name

		if (adsr != None): (attack,decay,sustain,release) = adsr
		self.set(attack=attack,decay=decay,sustain=sustain,release=release)
		self._defaultInSample = 1.0
		self._active          = False
		self._target          = 0.0

	def set(self,attack,decay,sustain,release):
		if   (attack  == None): attack  = UGen.defaultAttack
		elif (attack  <  1):    attack  = 1
		if   (decay   == None): decay   = UGen.defaultDecay
		elif (decay   <  1):    decay   = 1
		if   (sustain == None): sustain = UGen.defaultSustain
		if   (release == None): release = UGen.defaultRelease
		elif (release <  1):    release = 1
		self._attack   = attack
		self._decay    = decay
		self._sustain  = sustain
		self._release  = release

	def key_on(self,velocity=None,makeInterpolator=True):
		if (velocity == None): velocity = 1.0
		target1   = velocity
		target2   = velocity * self._sustain
		duration1 = self._attack
		duration2 = self._attack + self._decay
		xSplit    = duration1 / duration2
		self.trigger(target2,duration2,makeInterpolator=False)
		attackFunc = linear_ramp(0,xSplit,self._startVal,target1)
		decayFunc  = diminishing_exponential(xSplit,1,target1,target2)
		self._interpolator = piecewise([xSplit],[attackFunc,decayFunc])

	def key_off(self,makeInterpolator=True):
		self.trigger(0.0,self._release,makeInterpolator=False)
		self._interpolator = diminishing_exponential(0,1,0.0,self._target-self._startVal)

	#-- non-drivable attack, with side effects --

	@property
	def attack(self):
		return self._attack

	@attack.setter
	def attack(self,attack):
		self.set(attack,self.decay,self.sustain,self.release)

	#-- non-drivable decay, with side effects --

	@property
	def decay(self):
		return self._decay

	@decay.setter
	def decay(self,decay):
		self.set(self.attack,decay,self.sustain,self.release)

	#-- non-drivable sustain, with side effects --

	@property
	def sustain(self):
		return self._sustain

	@sustain.setter
	def sustain(self,sustain):
		self.set(self.attack,self.decay,sustain,self.release)

	#-- non-drivable release, with side effects --

	@property
	def release(self):
		return self._release

	@release.setter
	def release(self,release):
		self.set(self.attack,self.decay,self.sustain,release)
