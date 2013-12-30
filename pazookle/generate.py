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

from sys      import stderr
from math     import sin
from random   import Random
from ugen     import UGen
from util     import clip_value
from constant import twoPi


class Noise(UGen):
	"""White noise unit generator."""

	def __init__(self,inChannels=0,outChannels=1,name=None,
	             bias=None,gain=None,seed=None,subsample=None):
		super(Noise,self).__init__(inChannels=inChannels,outChannels=outChannels,name=name,
		                           bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "Noise.__init__(%s)" % name
		if (self.inChannels != 0):
			msg = "inChannels=%s is not valid for %s" % (self.inChannels,self)
			raise UGenError(msg)

		self._prng = Random()
		if (seed != None): self._prng.seed(seed)

		self._latest = 2*self._prng.random()-1
		if (self.outChannels == 2):
			self._latest2 = 2*self._prng.random()-1

		if (subsample == None):
			self.cycleScale = None
		else:                   
			self.cycleScale = float(subsample)
			self._cyclePos  = 0.0

	#-- tick handling --

	def tick(self):
		if (self.cycleScale != None):
			self._cyclePos += 1.0
			if (self._cyclePos < self.cycleScale):
				if (self.outChannels == 1): return self._latest
				else:                       return (self._latest,self._latest2)
			self._cyclePos %= self.cycleScale

		self._latest = 2*self._prng.random()-1
		if (self.outChannels == 1): return self._latest
		self._latest2 = 2*self._prng.random()-1
		return (self._latest,self._latest2)


class Periodic(UGen):
	"""Parent class for periodic unit generators (oscillators and others).

	Periodic ugens are characterized by their period (a duration), the scale
	at which they view one cycle in the period (e.g. 2pi for a sine), and a
	wave_generator function that maps a value within the period to an output
	value.

	Most periodic ugens can be created easily simply by overriding/extending
	the constructor to set the cycleScale and wave_generator.  The
	wave_generator should be a function that maps a value x to y, with
	0 <= x < cycleScale and, typically, -1 <= y <= 1.  The wave_generator can
	often be a simple lambda function, though it is also possible to define it
	as a method.
	$$$ currently, doing it as a method does not work
	"""

	def __init__(self,inChannels=0,outChannels=1,name=None,
	             bias=None,gain=None,freq=None,phase=None):
		super(Periodic,self).__init__(inChannels=inChannels,outChannels=outChannels,name=name,
		                              bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "Periodic.__init__(%s)" % name
		if (self.inChannels != 0) or (self.outChannels != 1):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		self.cycleScale     = 1.0
		self._cyclePos      = 0.0
		self.wave_generator = lambda x: x

		self._drivable += ["freq","phase"]
		self._freq  = self._freqLast  = 0.0  # overwritten by self.freq  = freq
		self._phase = self._phaseLast = 0.0  # overwritten by self.phase = phase
		if (freq  == None): freq  = UGen.defaultFreq
		if (phase == None): phase = UGen.defaultPhase
		self.freq  = freq
		self.phase = phase

	#-- drivable freq, with side effects --

	@property
	def freq(self):
		control = self._freq
		if (isinstance(control,UGen)): control = control.last
		if (control != self._freqLast): self._freq_update(control)
		return control

	@freq.setter
	def freq(self,val):
		self._freq_setter(val)

	def _freq_setter(self,val):
		if (isinstance(val,UGen)):
			self._drive("freq")
			self._freq += val
		else:
			# val is a scalar
			if (isinstance(self._freq,UGen)): del self._driven["freq"]
			self._freq_update(val)

	def _freq_update(self,val):
		self._freq = self._freqLast = float(val)
		# side effects
		if (self._freq == 0.0):
			self.period = 0.0
			self.step   = 0.0
		else:
			self.period = float(UGen.samplingRate) / self._freq
			self.step   = self.cycleScale / self.period
		if ("freq drive" in UGen.debug):
			print >>stderr, "  %s._freq_update(%s) -> period=%s step=%s" \
		                  % (self,val,self.period,self.step)

	#-- drivable phase, no side effects --

	@property
	def phase(self):
		control = self._phase
		if (isinstance(control,UGen)): control = control.last
		self._phaseLast = control
		return control

	@phase.setter
	def phase(self,val):
		self._phase_setter(val)

	def _phase_setter(self,val):
		if (isinstance(val,UGen)):
			self._drive("phase")
			self._phase += val
		else:
			# val is a scalar
			if (isinstance(self._phase,UGen)): del self._driven["phase"]
			self._phase = self._phaseLast = float(val)

	#-- tick handling --

	def tick(self):
		self._cyclePos = (self._cyclePos + self.step)  % self.cycleScale
		phasedPos      = (self._cyclePos + self.phase) % self.cycleScale
		if ("ticks" in UGen.debug):
			print >>stderr, "Periodic.tick(\"%s\") cyclePos=%s phasedPos=%s" \
			            % (self.name,self._cyclePos,phasedPos)
		return self.wave_generator(phasedPos)


class SinOsc(Periodic):
	"""Sinusoidal unit generator."""

	def __init__(self,inChannels=0,outChannels=1,name=None,
	             bias=None,gain=None,freq=None,phase=None):
		super(SinOsc,self).__init__(inChannels=inChannels,outChannels=outChannels,name=name,
		                            bias=bias,gain=gain,freq=freq,phase=phase)
		if ("constructors" in UGen.debug): print >>stderr, "SinOsc.__init__(%s)" % name
		self.cycleScale     = twoPi
		self.freq           = self._freq  # $$$ (this forces update needed when we changed cycleScale)
		self.wave_generator = lambda x: sin(x)


class SawOsc(Periodic):
	"""Sawtooth wave unit generator."""

	def __init__(self,inChannels=0,outChannels=1,name=None,
	             bias=None,gain=None,freq=None,phase=None):
		super(SawOsc,self).__init__(inChannels=inChannels,outChannels=outChannels,name=name,
		                            bias=bias,gain=gain,freq=freq,phase=phase)
		if ("constructors" in UGen.debug): print >>stderr, "SawOsc.__init__(%s)" % name
		self.cycleScale     = 1.0
		self.freq           = self._freq  # $$$ (this forces update needed when we changed cycleScale)
		self.wave_generator = lambda x: 2*x-1


class TriOsc(Periodic):
	"""Triangle wave unit generator."""

	def __init__(self,inChannels=0,outChannels=1,name=None,
	             bias=None,gain=None,freq=None,phase=None,duty=None):
		super(TriOsc,self).__init__(inChannels=inChannels,outChannels=outChannels,name=name,
		                            bias=bias,gain=gain,freq=freq,phase=phase)
		if ("constructors" in UGen.debug): print >>stderr, "TriOsc.__init__(%s)" % name

		self.cycleScale = 1.0
		self.freq       = self._freq  # $$$ (this forces update needed when we changed cycleScale)

		self._drivable += ["duty"]
		self._duty = self._dutyLast = 0.5  # overwritten by self.duty = duty
		if (duty == None): duty = 0.5
		self.duty = duty

	#-- drivable duty, with side effects --

	@property
	def duty(self):
		control = self._duty
		if (isinstance(control,UGen)):
			control = control.last
		if (control != self._dutyLast):
			self._duty_update(control)
		return control

	@duty.setter
	def duty(self,val):
		self._duty_setter(val)

	def _duty_setter(self,val):
		if (isinstance(val,UGen)):
			self._drive("duty")
			self._duty += val
		else:
			# val is a scalar
			if (isinstance(self._duty,UGen)): del self._driven["duty"]
			self._duty_update(val)

	def _duty_update(self,val):
		self._duty = self._dutyLast = val = clip_value(float(val),-1.0,1.0)
		# side effects
		if (val >= 1):                                   # right-leaning saw
			self.wave_generator = lambda x: 2*x-1
		elif (val <= 0):                                 # left-leaning saw
			self.wave_generator = lambda x: 1-2*x
		elif (val == 0.5):                               # triangle
			self.wave_generator = lambda x: (4*x-1) if (x<0.5) else (3-4*x)
		else:
			m1 = 2.0 / val
			m2 = 2.0 / (val-1)
			b2 = m2 + 1
			self.wave_generator = lambda x: (m1*x-1) if (x<val) else (m2*x-b2)

		if ("duty drive" in UGen.debug):
			print >>stderr, "  %s._duty_update(%s)" % (self,self._duty)


class SqrOsc(Periodic):
	"""Square wave unit generator."""

	def __init__(self,inChannels=0,outChannels=1,name=None,
	             bias=None,gain=None,freq=None,phase=None,duty=None):
		super(SqrOsc,self).__init__(inChannels=inChannels,outChannels=outChannels,name=name,
		                            bias=bias,gain=gain,freq=freq,phase=phase)
		if ("constructors" in UGen.debug): print >>stderr, "SqrOsc.__init__(%s)" % name

		self.cycleScale = 1.0
		self.freq       = self._freq  # $$$ (this forces update needed when we changed cycleScale)

		self._drivable += ["duty"]
		self._duty = self._dutyLast = 0.5  # overwritten by self.duty = duty
		if (duty == None): duty = 0.5
		self.duty = duty

	#-- drivable duty, with side effects --

	@property
	def duty(self):
		control = self._duty
		if (isinstance(control,UGen)):
			control = control.last
		if (control != self._dutyLast):
			self._duty_update(control)
		return control

	@duty.setter
	def duty(self,val):
		self._duty_setter(val)

	def _duty_setter(self,val):
		if (isinstance(val,UGen)):
			self._drive("duty")
			self._duty += val
		else:
			# val is a scalar
			if (isinstance(self._duty,UGen)): del self._driven["duty"]
			self._duty_update(val)

	def _duty_update(self,val):
		self._duty = self._dutyLast = val = clip_value(float(val),-1.0,1.0)
		# side effects
		if (val >= 1):                       # all-off duty cycle
			self.wave_generator = lambda x: -1
		elif (val <= 0):                     # all-on duty cycle
			self.wave_generator = lambda x: 1
		else:
			self.wave_generator = lambda x: 1 if (x<val) else -1

		if ("duty drive" in UGen.debug):
			print >>stderr, "  %s._duty_update(%s)" % (self,self._duty)


class ImpulseTrain(UGen):
	"""Generator for a periodic one-sample wide pulse."""

	def __init__(self,inChannels=0,outChannels=1,name=None,
	             bias=None,gain=None,freq=None):
		super(ImpulseTrain,self).__init__(inChannels=inChannels,outChannels=outChannels,name=name,
		                                  bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "ImpulseTrain.__init__(%s)" % name
		if (self.inChannels != 0) or (self.outChannels != 1):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		self.cycleScale = 1.0
		self._cyclePos  = 0.0

		self._drivable += ["freq"]
		self._freq = self._freqLast  = 0.0  # overwritten by self.freq  = freq
		if (freq == None): freq  = UGen.defaultFreq
		self.freq = freq

	#-- drivable freq, with side effects --

	@property
	def freq(self):
		control = self._freq
		if (isinstance(control,UGen)): control = control.last
		if (control != self._freqLast): self._freq_update(control)
		return control

	@freq.setter
	def freq(self,val):
		self._freq_setter(val)

	def _freq_setter(self,val):
		if (isinstance(val,UGen)):
			self._drive("freq")
			self._freq += val
		else:
			# val is a scalar
			if (isinstance(self._freq,UGen)): del self._driven["freq"]
			self._freq_update(val)

	def _freq_update(self,val):
		self._freq = self._freqLast = float(val)
		# side effects
		if (self._freq == 0.0):
			self.period = 0.0
			self.step   = 0.0
		else:
			self.period = float(UGen.samplingRate) / self._freq
			self.step   = self.cycleScale / self.period
		if ("freq drive" in UGen.debug):
			print >>stderr, "  %s._freq_update(%s) -> period=%s step=%s" \
		                  % (self,val,self.period,self.step)

	#-- tick handling --

	def tick(self):
		self._cyclePos = self._cyclePos + self.step
		if (self._cyclePos < self.cycleScale): # haven't met period, so no pulse
			return 0.0
		self._cyclePos %= self.cycleScale      # reduce position modulo the period
		return 1.0                             # output a single-sample pulse

