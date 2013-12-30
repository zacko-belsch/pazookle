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

from sys    import stderr
from math   import floor,ceil
from array  import array
from wave   import open as wave_open
from struct import unpack as struct_unpack
from ugen   import UGen,UGraph,PassThru,Mixer
from util   import clip_value,raise_to_mulitple


class Delay(UGen):
	"""A delay buffer.

	This class is useful for building feedbacks for reverberation as well as
	implementing separate delays for different paths through a chain.

	Note that as of this writing, classes that would facilitate feeding left
	and right channels into separate delay elements are not yet implemented.
	"""
	# $$$ make another version that has floating point read/write index, and
	# $$$ .. takes floor before reading and writing;  this is an approximation
	# $$$ .. to a floating point delay

	def __init__(self,delay=None,channels=1,name=None,
		         bias=0.0,gain=1.0):
		super(Delay,self).__init__(inChannels=channels,outChannels=channels,name=name,
		                           bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "Delay.__init__(%s)" % name
		if (self.inChannels != self.outChannels):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		if (delay == None) or (delay < 1): delay = 1
		self._bufferLen = None
		self._buffer    = None
		self._buffer2   = None
		self.delay = delay

	#-- non-drivable delay, with side effects --

	@property
	def delay(self):
		return self._delay

	@delay.setter
	def delay(self,delay):
		self._delay = float(delay)
		# side effects
		self._delayCeil = int(ceil(delay))
		bufferLen       = raise_to_mulitple(self._delayCeil,UGen.bufferChunks)
		if (self._buffer == None):
			# initial buffer setup
			self._buffer = array("d", [0.0]*bufferLen)
			if (self.inChannels == 2):
				self._buffer2 = array("d", [0.0]*bufferLen)
			self._bufferLen = bufferLen
			self._writeIx    = 0
		elif (bufferLen > self._bufferLen):
			# increased buffer
			self._buffer.extend([0.0]*(bufferLen-self._bufferLen))
			if (self.inChannels == 2):
				self._buffer2.extend([0.0]*(bufferLen-self._bufferLen))
			self._bufferLen = bufferLen
		self._readIx = (self._writeIx - self._delayCeil) % bufferLen

	#-- tick handling --

	def tick(self,sample,sample2=None):
		# read before write, since readIx and writeIx may be the same
		outSample = self._buffer[self._readIx]
		self._buffer[self._writeIx] = sample
		if (sample2 != None):
			outSample2 = self._buffer2[self._readIx]
			self._buffer2[self._writeIx] = sample2

		if ("Delay" in UGen.debug):
			print >>stderr, "Delay.tick(\"%s\") %s -> buffer[%d]  buffer[%d]  -> %s" \
			              % (self.name,self._writeIx,sample,self._readIx,outSample)
		if ("Delay" in UGen.debug) and (sample2 != None):
			print >>stderr, "Delay.tick(\"%s\") %s -> buffer2[%d] buffer2[%d] -> %s" \
			              % (self.name,self._writeIx,sample2,self._readIx,outSample2)

		self._readIx  = (self._readIx+1)  % self._bufferLen
		self._writeIx = (self._writeIx+1) % self._bufferLen

		if (sample2 == None): return outSample
		else:                 return (outSample,outSample2)


class Echo(UGraph):
	"""Echo effect, built from Delay and Mixer objects.

	Note that the mix control is 0 for 100% dry, and 1 for 100% wet
	"""

	def __init__(self,name=None,delay=None,channels=1,gain=1.0,mix=0.5):
		super(Echo,self).__init__(name=name)

		if (delay == None) or (delay < 1): delay = 1
		self._delay = delay

		# nota bene: the first feed into mixer is our feedback;  all remaining
		#            feeds will come from the outside;  the Mixer object
		#            considers the first feed as "dry", which is the opposite
		#            of our use here
		self.inlet  = self._mixer = mixer = Mixer(channels=channels)
		self.outlet = self._echo  = echo  = Delay(delay,channels=channels)
		mixer >> echo >> mixer

		self.gain = gain
		self.mix  = mix

	#-- setters and getters --
	# $$$ need setter/getter for delay length

	@property
	def gain(self):
		return self._gain

	@gain.setter
	def gain(self,gain):
		self._gain = gain
		if (hasattr(self,"_mixer")):
			self._mixer.gain = gain

	@property
	def mix(self):
		return self._mix

	@mix.setter
	def mix(self,mix):
		self._mix = mix = clip_value(float(mix),-1.0,1.0)
		if (hasattr(self,"_mixer")):
			self._mixer.wet = (1-mix)      # (this is the external input)
			self._mixer.dry = mix          # (this is the echo feedback)


class Clip(UGen):
	"""An audio clip, for load and playback.

	An audio clip is consists of a buffer loaded with a waveform from a .wav
	file.  We allow playback through the buffer at any rate, forward or
	backward.

	If a source is provided at instantiation the load happens immediately to
	fill the buffer.  Otherwise, the caller can call the load() method. 
	Normally source is a string indicating a .wav file.  But source can also be
	a list, in which case we load from the list instead of reading a file. 
	Note that we perform no scaling for values in lists;  we typically expect
	them to range from -1.0 to +1.0.

	Assigning a value to rate sets the playback rate.  A rate of 1.0 will
	playback a normal speed, 1.5 plays 50% faster, and so on.  Negative rates
	will playback in reverse.  Playback is initiated with a call to the
	trigger() method.  The rate *can* be altered during playback.

	An additional control, skip, allows some portion of the waveform to be
	skipped when triggered.  Note that skip is clipped so that 0<=skip<=1. 
	Also note that the duration method does *not* take into account the fact
	that some of the waveform might be skipped.

	Note that rate=0 is allowed.
	"""
	# $$$ .skip does not work with .interpolation
	# $$$ we'd like to allow any iterable as source

	def __init__(self,source=None,name=None,
		         bias=0.0,gain=1.0,rate=None,skip=None,
		         interpolate=True,loop=False):
		super(Clip,self).__init__(inChannels=0,outChannels=1,name=name,
		                          bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "Clip.__init__(%s)" % name
		self.source      = source
		self._buffer     = None
		self._buffer2    = None
		self._bufferUsed = 0
		self._active     = False

		self.interpolate = interpolate
		self.loop        = loop

		self._drivable = ["rate","skip"]
		self._rate = self._rateLast = 0.0  # overwritten by self.rate = rate
		self._skip = self._skipLast = 0.0  # overwritten by self.skip = skip
		if (rate == None): rate = 1.0
		if (skip == None): skip = 0.0
		self.rate = rate
		self.skip = skip

		if (source != None): self.load(source)

	def __len__(self):
		return self._bufferUsed

	def duration(self):
		if (self.rate == 0): return float("inf")
		return ceil(self._bufferUsed / abs(self.rate))

	def trigger(self):
		if (self._bufferUsed == 0):
			msg = "%s can't trigger with an empty buffer" % self
			raise UGenError(msg)
		if (self.rate >= 0): self.position =    self.skip  * self._bufferUsed
		else:                self.position = (1-self.skip) * self._bufferUsed
		self._active = True

	#-- buffer load --

	def load(self,source=None):
		if (source == None):
			source = self.source
		if (source == None):
			msg = "%s can't read an unnamed wav file" % self
			raise UGenError(msg)
		if (type(source) in [list,tuple]): self._load_from_list(source)
		else:                              self._load_from_file(source)

	def _load_from_file(self,source):
		self.filename = source
		self.wavFile  = wavFile = wave_open(self.filename, "rb")

		channels     = wavFile.getnchannels()
		sampleWidth  = wavFile.getsampwidth()
		samplingRate = wavFile.getframerate()
		numSamples   = wavFile.getnframes()
		compName     = wavFile.getcompname()

		if (channels not in [1,2]):
			msg = "for \"%s\", channels=%d is not supported" \
			    % (self.filename,channels)
			raise UGenError(msg)
		if (sampleWidth not in [1,2]):
			msg = "for \"%s\", sampleWidth=%d is not supported" \
			    % (self.filename,sampleWidth)
			raise UGenError(msg)
		if (samplingRate != UGen.samplingRate):
			msg = "for \"%s\", samplingRate=%s does not match %s" \
			   % (self.filename,samplingRate)
			raise UGenError(msg)
		if (compName != "not compressed"):
			msg = "for \"%s\", compName=\"%s\" is not supported" \
			    % (self.filename,compName)
			raise UGenError(msg)

		self.inChannels  = 0
		self.outChannels = channels
		sampleScale = (1<<(8*sampleWidth-1)) - 1
		if (sampleWidth == 1): packFormat = "b"
		else:                  packFormat = "h"
		if (channels == 2):    packFormat = "2%s" % packFormat

		self._allocate(numSamples)

		if ("Clip" in UGen.debug):
			print >>stderr, "Clip.load(%s)" % self
			print >>stderr, "  channels    = %s" % channels
			print >>stderr, "  numSamples  = %s" % numSamples
			print >>stderr, "  sampleWidth = %s" % sampleWidth
			print >>stderr, "  sampleScale = %s" % sampleScale
			print >>stderr, "  packFormat  = %s" % packFormat

		if (channels == 1):
			for ix in xrange(numSamples):
				sample = wavFile.readframes(1)
				sample = struct_unpack(packFormat,sample)[0]
				if (sample < -sampleScale): sample = -sampleScale
				self._buffer[ix] = sample / float(sampleScale)
		else: # (channels == 2):
			for ix in xrange(numSamples):
				sample = wavFile.readframes(1)
				(sample,sample2) = struct_unpack(packFormat,sample)
				if (sample  < -sampleScale): sample  = -sampleScale
				if (sample2 < -sampleScale): sample2 = -sampleScale
				self._buffer [ix] = sample  / float(sampleScale)
				self._buffer2[ix] = sample2 / float(sampleScale)

		wavFile.close()

	def _load_from_list(self,listVariable):
		numSamples = len(listVariable)
		datum = listVariable[0]
		if (type(datum) in [list,tuple]): channels = len(datum)
		else:                             channels = 1
	
		if (type(listVariable) == list):
			self.filename = "%dx%d list" % (numSamples,channels)
		elif (type(listVariable) == tuple):
			self.filename = "%dx%d tuple" % (numSamples,channels)
		else:
			assert (False), \
			       "internal error: attempt to load a Clip from a %s" \
			     % type(listVariable)

		self.wavFile = None

		if (channels not in [1,2]):
			msg = "for \"%s\", channels=%d is not supported" \
			    % (self.filename,channels)
			raise UGenError(msg)

		self.inChannels  = 0
		self.outChannels = channels
		self._allocate(numSamples)

		if ("Clip" in UGen.debug):
			print >>stderr, "Clip.load(%s)" % self
			print >>stderr, "  channels    = %s" % channels
			print >>stderr, "  numSamples  = %s" % numSamples

		if (channels == 1):
			for ix in xrange(numSamples):
				self._buffer[ix] = listVariable[ix]
		else: # (channels == 2):
			for ix in xrange(numSamples):
				(sample,sample2) = listVariable[ix]
				self._buffer [ix] = sample
				self._buffer2[ix] = sample2

	def _allocate(self,numSamples):
		if (self._buffer == None):
			self._buffer = array("d", [0.0]*numSamples)
		elif (numSamples > len(self._buffer)):
			self._buffer.extend([0.0]*(numSamples-len(self._buffer)))
		if (self.outChannels == 2):
			if (self._buffer2 == None):
				self._buffer2 = array("d", [0.0]*numSamples)
			elif (numSamples > len(self._buffer2)):
				self._buffer2.extend([0.0]*(numSamples-len(self._buffer2)))
		self._bufferUsed = numSamples

	#-- drivable rate, no side effects --

	@property
	def rate(self):
		control = self._rate
		if (isinstance(control,UGen)): control = control.last
		self._rateLast = control
		return control

	@rate.setter
	def rate(self,val):
		self._rate_setter(val)

	def _rate_setter(self,val):
		if (isinstance(val,UGen)):
			self._drive("rate")
			self._rate += val
		else:
			# val is a scalar
			if (isinstance(self._rate,UGen)): del self._driven["rate"]
			self._rate = self._rateLast = float(val)

	#-- drivable skip, no side effects --

	@property
	def skip(self):
		control = self._skip
		if (isinstance(control,UGen)): control = control.last
		self._skipLast = control
		return control

	@skip.setter
	def skip(self,val):
		self._skip_setter(val)

	def _skip_setter(self,val):
		val = clip_value(val,0.0,1.0)
		if (isinstance(val,UGen)):
			self._drive("skip")
			self._skip += val
		else:
			# val is a scalar
			if (isinstance(self._skip,UGen)): del self._driven["skip"]
			self._skip = self._skipLast = float(val)

	#-- tick handling --

	def tick(self):
		ix = None
		if (self._active):
			if (self.rate >= 0):
				# forward play, fetch then increment
				ix = int(floor(self.position))
				frac = self.position - ix
				self.position += self.rate
				if (self.position < self._bufferUsed):
					pass
				elif (self.loop):
					self.position %= self._bufferUsed
				else:
					self._active = False
			else: # (self.rate < 0):
				# reverse play, increment then fetch
				self.position += self.rate
				if (self.position >= 0):
					ix = int(floor(self.position))
					frac = self.position - ix
				elif (self.loop):
					self.position %= self._bufferUsed
				else:
					self._active = False

		if (ix == None):
			outSample = outSample2 = 0.0
		elif (self.interpolate):
			iy = (ix+1) % self._bufferUsed
			outSample = self._buffer[ix] \
			          + frac * (self._buffer[iy] - self._buffer[ix])
			if (self.outChannels == 2):
				outSample2 = self._buffer2[ix] \
				           + frac * (self._buffer2[iy] - self._buffer2[ix])
		else:
			outSample = self._buffer[ix]
			if (self.outChannels == 2):
				outSample2 = self._buffer2[ix]

		if (self.outChannels == 1): return outSample
		else:                       return (outSample,outSample2)


class Capture(PassThru):
	"""Capture input value(s) into a list object.

	The "output" is a standard python list object, either a list of floats or
	a list of float tuples (left-right pairs).  The user can get a copy of the
	list at any time with the buffer() method.

	"Recording" capability can be turned on and off with on() and off()
	methods.  By default recording is on when the object is created.  The
	buffer can be erased with the erase() method.  For compatability with
	similar objects, trigger() is provided as a synonym for on().
	"""
	# $$$ use array instead of list; allocate buffer in chunks

	def __init__(self,channels=1,on=True,name=None):
		super(Capture,self).__init__(channels=channels,name=name)
		if ("constructors" in UGen.debug): print >>stderr, "Capture.__init__(%s)" % name
		self.ignoreInputlessSink = True
		self.sampleNum = 0
		self.erase()
		self._active = False
		if (on): self.on()

	def buffer(self):
		return list(self._buffer)

	def erase(self):
		self._buffer = []

	def trigger(self):
		self.on()

	def on(self):
		UGen.add_sink(self)
		self._active = True

	def off(self):
		UGen.remove_sink(self)
		self._active = False

	def tick(self,sample,sample2=None):
		if (self._active):
			if (sample2 == None): self._buffer += [sample]
			else:                 self._buffer += [(sample,sample2)]

		if (sample2 == None): return sample
		else:                 return (sample,sample2)
