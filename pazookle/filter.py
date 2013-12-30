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

from math import cos,tan
from ugen import UGen


class LowPass(UGen):
	"""Resonant low pass filter.  2nd order Butterworth.

	This also serves as the parent class for other pass/reject filters

	Adapted from ChucK's rlpf implementation, equivalent to ChucK's LPF.
	"""
	# $$$ freq and Q should be drivable

	def __init__(self,name=None,
		         bias=0.0,gain=1.0,freq=None,Q=None):
		super(LowPass,self).__init__(inChannels=1,outChannels=1,name=name,
		                             bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "LowPass.__init__(%s)" % name
		if (self.inChannels != 1) and (self.outChannels != 1):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		self._y2 = 0.0
		self._y1 = 0.0
		self.set(freq,Q)

	def set(self,freq,Q):
		if (freq == None): freq = UGen.defaultFilterFreq
		if (Q    == None): Q    = UGen.defaultFilterQ
		self._freq = freq = float(freq)
		self._Q    = Q    = float(min(Q,1000))
		f = freq * UGen.radiansPerSample
		d = tan(f/(2*Q))
		c = (1-d) / (1+d)
		self._b1 = b1 = (1+c) * cos(f)
		self._b2 = -c
		self._a0 = (1+c-b1)/4

	#-- non-drivable freq, with side effects --

	@property
	def freq(self):
		return self._freq

	@freq.setter
	def freq(self,freq):
		self.set(freq,self.Q)

	#-- non-drivable Q, with side effects --

	@property
	def Q(self):
		return self._Q

	@Q.setter
	def Q(self,Q):
		self.set(self.freq,Q)

	#-- tick handling --

	def tick(self,sample):
		y0        = self._b2 * self._y2 \
		          + self._b1 * self._y1 \
		          + self._a0 * sample
		outSample = y0 \
		          + 2*self._y1 \
		          + self._y2
		self._y2  = self._y1
		self._y1  = y0
		return outSample


class HighPass(LowPass):
	"""Resonant high pass filter.  2nd order Butterworth.

	Adapted from ChucK's rhpf implementation, equivalent to ChucK's HPF.
	"""

	def set(self,freq,Q):
		if (freq == None): freq = UGen.defaultFilterFreq
		if (Q    == None): Q    = UGen.defaultFilterQ
		self._freq = freq = float(freq)
		self._Q    = Q    = float(min(Q,1000))
		f = freq * UGen.radiansPerSample
		d = tan(f/(2*Q))
		c = (1-d) / (1+d)
		self._b1 = b1 = (1+c) * cos(f)
		self._b2 = -c
		self._a0 = (1+c+b1)/4

	#-- tick handling --

	def tick(self,sample):
		y0        = self._b2 * self._y2 \
		          + self._b1 * self._y1 \
		          + self._a0 * sample
		outSample = y0 \
		          - 2*self._y1 \
		          + self._y2
		self._y2  = self._y1
		self._y1  = y0
		return outSample


class BandPass(LowPass):
	"""Band pass filter.  2nd order Butterworth.

	Adapted from ChucK's bpf implementation, equivalent to ChucK's BPF.
	"""

	def set(self,freq,Q):
		if (freq == None): freq = UGen.defaultFilterFreq
		if (Q    == None): Q    = UGen.defaultFilterQ
		self._freq = freq = float(freq)
		self._Q    = Q    = float(Q)
		f = freq * UGen.radiansPerSample
		c = 1 / tan(f/(2*Q))
		self._a0 = a0 = 1 / (1+c)
		self._b1 = 2 * cos(f) * c * a0
		self._b2 = (1-c) * a0

	#-- tick handling --

	def tick(self,sample):
		y0        = self._b2 * self._y2 \
		          + self._b1 * self._y1 \
		          + sample
		outSample = self._a0 * (y0 - self._y2)
		self._y2  = self._y1
		self._y1  = y0
		return outSample


class BandReject(LowPass):
	"""Band reject filter.  2nd order Butterworth.

	Adapted from ChucK's brf implementation, equivalent to ChucK's BRF.
	"""

	def set(self,freq,Q):
		if (freq == None): freq = UGen.defaultFilterFreq
		if (Q    == None): Q    = UGen.defaultFilterQ
		self._freq = freq = float(freq)
		self._Q    = Q    = float(Q)
		f = freq * UGen.radiansPerSample
		c = tan(f/(2*Q))
		self._a0 = a0 = 1 / (1+c)
		self._b1 = -2 * cos(f) * a0
		self._b2 = (1-c) * a0

	#-- tick handling --

	def tick(self,sample):
		y0        = sample \
		          - self._b2 * self._y2 \
		          - self._b1 * self._y1
		outSample = self._a0 * (y0 + self._y2) \
		          + self._b1 * self._y1
		self._y2  = self._y1
		self._y1  = y0
		return outSample


class ResonZ(LowPass):
	"""Two pole resonant filter with poles at z = {-1,+1}.

	References:
	[1] Steiglitz, "A Note on Constant-Gain Digital Resonators", Computer
	    Music Journal, 18:4, pp 8-10.
	"""

	def set(self,freq,Q):
		"""see reference [1]"""
		if (freq == None): freq = UGen.defaultFilterFreq
		if (Q    == None): Q    = UGen.defaultFilterQ
		self._freq = freq = float(freq)
		self._Q    = Q    = float(Q)
		f  = freq * UGen.radiansPerSample
		r  = 1 - (f / (2*Q))
		r2 = r * r
		c  = (2*r*cos(f)) / (r2+1)
		self._b1 = 2*r*c
		self._b2 = -r2
		self._a0 = (1-r2) / 2

	#-- tick handling --

	def tick(self,sample):
		y0        = self._b2*self._y2 \
		          + self._b1*self._y1 \
		          + sample
		outSample = self._a0 * (y0 - self._y2)
		self._y2  = self._y1
		self._y1  = y0
		return outSample


class OnePole(UGen):
	"""One-pole digital filter."""
	# $$$ pole should be drivable
	# $$$ this has not been tested

	def __init__(self,name=None,
		         bias=0.0,gain=1.0,pole=None):
		super(OnePole,self).__init__(inChannels=1,outChannels=1,name=name,
		                             bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "OnePole.__init__(%s)" % name
		if (self.inChannels != 1) and (self.outChannels != 1):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		self._y1 = 0.0
		self.set(pole)

	def set(self,pole):
		if (pole == None): pole = UGen.defaultFilterPole
		self._pole = pole = float(pole)
		self._b0 = 1-abs(pole)
		self._a1 = -pole

	#-- non-drivable pole, with side effects --

	@property
	def pole(self):
		return self._pole

	@pole.setter
	def pole(self,pole):
		self.set(pole)

	#-- tick handling --

	def tick(self,sample):
		y0       = self._b0 * sample \
		         - self._a1 * self._y1
		self._y1 = y0
		return y0


class OneZero(UGen):
	"""One-zero digital filter."""
	# $$$ zero should be drivable
	# $$$ this has not been tested

	def __init__(self,name=None,
		         bias=0.0,gain=1.0,zero=None):
		super(OneZero,self).__init__(inChannels=1,outChannels=1,name=name,
		                             bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "OneZero.__init__(%s)" % name
		if (self.inChannels != 1) and (self.outChannels != 1):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		self._w1 = 0.0
		self.set(zero)

	def set(self,zero):
		if (zero == None): zero = UGen.defaultFilterZero
		self._zero = zero = float(zero)
		self._b0 = 1/(1+abs(zero))
		self._b1 = -zero * self._b0

	#-- non-drivable zero, with side effects --

	@property
	def zero(self):
		return self._zero

	@zero.setter
	def zero(self,zero):
		self.set(zero)

	#-- tick handling --

	def tick(self,sample):
		y0       = self._b0 * sample \
		         + self._b1 * self._w1
		self._w1 = sample
		return y0


class BiQuad(UGen):
	"""Two-pole, two-zero digital filter."""
	# $$$ poles and zeros should be drivable
	# $$$ this has not been tested

	def __init__(self,name=None,
		         bias=0.0,gain=1.0,
		         pole=None,poleRadius=None,zero=None,zeroRadius=None,
		         normalize=False):
		super(BiQuad,self).__init__(inChannels=1,outChannels=1,name=name,
		                            bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "BiQuad.__init__(%s)" % name
		if (self.inChannels != 1) and (self.outChannels != 1):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		self.normalize = normalize
		self._w1 = self._w2 = 0.0
		self._y1 = self._y2 = 0.0
		set_notch    (self,zero,zeroRadius)
		set_resonance(self,pole,poleRadius)

	def set_notch(self,zero,radius):
		if (zero   == None): zero   = UGen.defaultFilterZero
		if (radius == None): radius = 0.0
		self._zeroFreq   = zero   = float(zero)
		self._zeroRadius = radius = float(radius)
		self._b0 = 1.0
		self._b1 = -2 * radius * cos(zero * UGen.radiansPerSample)
		self._b2 = radius * radius

	def set_resonance(self,pole,radius):
		if (pole   == None): pole   = UGen.defaultFilterPole
		if (radius == None): radius = 0.0
		self._poleFreq   = pole   = float(pole)
		self._poleRadius = radius = float(radius)
		self._a0 = 1.0
		self._a1 = -2 * radius * cos(pole * UGen.radiansPerSample)
		self._a2 = radius * radius

		if (self.normalize):
			self._b0 = b0 = (1-self._a2)/2
			self._b1 = -1.0
			self._b2 = -b0

	#-- tick handling --

	def tick(self,sample):
		w0       = self._a0 * sample
		y0       = self._b0 *       w0 \
		         + self._b1 * self._w1 \
		         + self._b2 * self._w2 \
		         - self._a2 * self._y2 \
		         - self._a1 * self._y1
		self._w2 = self._w1
		self._w1 = w0
		self._y2 = self._y1
		self._y1 = y0
		return y0


class ZeroCross(UGen):
	"""Zero crossing filter.

	Ouputs a single pulse at each zero crossing, with the sign indicating the
	the direction of the crossing.
	"""

	def __init__(self,channels=1,name=None,
		         bias=0.0,gain=1.0):
		super(ZeroCross,self).__init__(inChannels=channels,outChannels=channels,name=name,
		                               bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "ZeroCross.__init__(%s)" % name
		if (self.inChannels != self.outChannels):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		self._latest  = 0.0
		self._latest2 = 0.0

	#-- tick handling --

	def tick(self,sample,sample2=None):
		if   (self._latest < 0) and (sample >= 0): outSample =  1.0
		elif (self._latest > 0) and (sample <= 0): outSample = -1.0
		else:                                      outSample =  0.0

		if (sample2 != None):
			if   (self._latest2 < 0) and (sample2 >= 0): outSample2 =  1.0
			elif (self._latest2 > 0) and (sample2 <= 0): outSample2 = -1.0
			else:                                        outSample2 =  0.0

		self._latest = sample
		if (sample2 == None): return outSample
		self._latest2 = sample2
		return (outSample,outSample2)
