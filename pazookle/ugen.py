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
from math     import ceil,pi,sin,cos
from util     import clip_value
from constant import sqrt2,halfSqrt2,twoPi,quarterPi


class UGenError(Exception):
	def __init__(self,message):
		Exception.__init__(self,message)


class UGen(object):
	"""Parent class for unit generators

	Unit generators (a.k.a "ugens") can be linked together to form chains.
	Syntactically this is accomplished using the >> operator, like this:
		oscillator >> envelope >> wavefile
	where oscillator, envelope, and wavefile are instances of ugens (i.e. they
	have been previously instatiated).  Ugens can have multiple inputs linked
	to them, and these are usually just summed.  There aren't many restrictions
	on linkage, and feedback loops are allowed.

	Each ugen can have up to two input and output channels, and the number
	doesn't have to match.  The pipeline percolation computation automatically
	takes care of duplicating a mono output that is fed to a stereo input, and
	averaging stereo fed to mono.  When we have stero, we consider the first
	channel as the left, the second as the right.

	All ugens have controls for bias and gain, and all periodic ugens (subclass
	Periodic) have frequency and phase.  The default behavior is that these are
	all "off" at construction.  Thus all ugens are born silent.  Each of these
	four controls can be driven by the output of a ugen chain by using item
	lookup syntax, like this:
		fmModulator >> fmCarrier["freq"] >> wavefile

	Samples in the pipeline are floating point values.  We expect the typical
	range to be from -1.0 to +1.0, but generally there's nothing that requires
	that.

	Debug settings as of this writing:
		constructors:  track __init__ call chain
		feeds:         creation an management of ugen-to-ugen feeds and drives
		+connection:   connections made with += syntax
		drivables:     related to drivable controls
		pipeline:      values percolating through the pipeline
		ticks:         values percolating through process_tick() and tick()
		envelopes:     values of envelopes
		resolution:    related to sample resolution
		Step:          related to Step class
		Delay:         related to Delay class
		Clip:          related to Clip class
		pan drive:     related to drivable .pan control
		freq drive:    related to drivable .freq control
		duty drive:    related to drivable .duty control
		stifle ids:    don't show id numbers in ugen names
	"""

	id                = 0
	debug             = {}
	shreduler         = None
	samplingRate      = 0.0
	defaultBias       = 0.0    # $$$ add static methods to set these
	defaultGain       = 0.0
	defaultFreq       = 0.0
	defaultPhase      = 0.0
	defaultPan        = 0.0
	defaultAttack     = None   # (attack,decay,release are set from sampling rate)
	defaultDecay      = None
	defaultSustain    = 0.5
	defaultRelease    = None
	defaultFilterFreq = 1000.0
	defaultFilterQ    = 1.0
	defaultFilterPole = 0.9
	defaultFilterZero = -0.9
	bufferChunks      = 1024

	@staticmethod
	def set_debug(debugNames):
		if (type(debugNames) not in (list,tuple)): debugNames = [debugNames]
		for debugName in debugNames: UGen.debug[debugName] = True

	@staticmethod
	def unset_debug(debugNames):
		if (type(debugNames) not in (list,tuple)): debugNames = [debugNames]
		for debugName in debugNames:
			try: del UGen.debug[debugName]
			except KeyError: pass

	@staticmethod
	def set_shreduler(shreduler):
		UGen.shreduler = shreduler
		UGen._set_sampling_rate(shreduler.samplingRate)

	@staticmethod
	def set_sampling_rate(samplingRate):
		UGen._set_sampling_rate(samplingRate)

	@staticmethod # this is not intended to be public
	def _set_sampling_rate(samplingRate):
		UGen.samplingRate     = samplingRate
		UGen.radiansPerSample = twoPi / UGen.samplingRate
		UGen.defaultAttack    = 0.100 * samplingRate
		UGen.defaultDecay     = 0.100 * samplingRate
		UGen.defaultRelease   = 0.100 * samplingRate

	@staticmethod
	def pipeline_change():
		if (UGen.shreduler != None): UGen.shreduler.pipeline_change()

	@staticmethod
	def add_sink(sink):
		if (UGen.shreduler != None): UGen.shreduler.add_sink(sink)

	@staticmethod
	def remove_sink(sink):
		if (UGen.shreduler != None): UGen.shreduler.remove_sink(sink)

	#-- construction --

	def __init__(self,inChannels=1,outChannels=None,name=None,
	             bias=None,gain=None):
		UGen.id += 1
		self.id = UGen.id
		if (name == None): name = "%s.%s" % (self.__class__.__name__,self.id)
		self.name = name
		if ("constructors" in UGen.debug): print >>stderr, "UGen.__init__(%s) id=%d" % (name,self.id)

		self._feeds    = []            # a list of ugens feeding input into
		                               # .. this, EXcluding driven controls;
		                               # .. list elements are tuples, either
		                               # .. a (ugen,) single or a (ugen,channel)
		                               # .. pair, where channel is one of "L>",
		                               # .. "R>", ">L", ">R", "L>L", "R>R",
		                               # .. "L>R" or "R>L"
		self._driven   = {}            # map from a driven control to the ugen
		                               # .. driving it
		self._drives   = None          # an (ugen,controlName) pair
		                               # .. indicating a control this ugen
		                               # .. drives (usually None)

		self.ignoreInputlessSink = False	# true means ignore this as a sink
											# .. if it has no input

		if (not (0 <= inChannels <= 2)):
			msg = "inChannels=%s is not valid for %s" % (inChannels,self)
			raise UGenError(msg)
		if (outChannels != None) and (not (1 <= outChannels <= 2)):
			msg = "outChannels=%s is not valid for %s" % (outChannels,self)
			raise UGenError(msg)
		self.inChannels = inChannels
		self._defaultInSample = 0.0

		if (outChannels == None):
			if (inChannels == 0): outChannels = 1
			else:                 outChannels = inChannels
		self.outChannels = outChannels

		self._feedsNeeded = 1

		self._drivable = ["bias","gain"]
		self._bias = self._biasLast = 0.0  # overwritten by self.bias = bias
		self._gain = self._gainLast = 0.0  # overwritten by self.gain = gain
		if (bias == None): bias = UGen.defaultBias
		if (gain == None): gain = UGen.defaultGain
		self.bias = bias
		self.gain = gain

		self.last  = 0.0
		self.last2 = 0.0

	#-- identification --

	def __str__(self):
		if ("stifle ids" in UGen.debug): return self.name
		else:                            return "%s:%s" % (self.id,self.name)

	def transcript(self,extra=None):
		if (extra == None): extra = []
		s = [str(self)]
		if ("class" in extra): s += [self.__class__.__name__]
		if (self._driven.keys != []):
			for controlName in self._driven:
				s += ["%s[%s]" % (controlName,self._driven[controlName])]
		if (self._feeds != []):
			feedsStr = []
			for feed in self._feeds:
				if (len(feed) == 1): feedsStr += [str(feed[0])]
				else:                feedsStr += ["(%s)"%",".join(map(str,feed))]
			s += ["in[%s]" % ",".join(feedsStr)]
		if (self._drives != None):
			(upstream,controlName) = self._drives
			s += ["drives[%s.%s]" % (upstream,controlName)]
		return " ".join(s)

	#-- connection syntax --

	def __rshift__(self,downstream):
		if ("feeds" in UGen.debug): print >>stderr, "__rshift__(%s,%s)" % (self,downstream)
		if (type(downstream) in (list,tuple)):
			for element in downstream: self >> element
			return downstream

		upstream = self
		if (upstream._drives != None): (upstream,_) = upstream._drives
		if (isinstance(downstream,UChannel)):
			downstream.ugen.add_feed(upstream,intoChannel=downstream.channelId)
			return downstream
		if (isinstance(downstream,UGen)):
			downstream.add_feed(upstream)
			return downstream
		msg = "cannot connect %s to %s, the latter is not a UGen" % (upstream,downstream)
		raise UGenError(msg)

	def __iadd__(self,upstream):
		if (type(upstream) in (list,tuple)):
			for element in upstream: self += element
			return self

		if (not isinstance(upstream,UGen)):
			msg = "cannot connect %s to %s, the former is not a UGen" % (upstream,self)
			raise UGenError(msg)
		if (upstream._drives != None):
			msg = "cannot connect %s to %s, the former is an internal UGen" % (upstream,self)
			raise UGenError(msg)
		if ("+connection" in UGen.debug):
			print >>stderr, "%s += %s" % (self,upstream)
		self.add_feed(upstream)
		return self

	def __getitem__(self,controlName):
		if (controlName in ["left","right"]):
			return UChannel(self,controlName)
		if (controlName not in self._drivable):
			msg = "%s[\"%s\"] is not a drivable control for that type of UGen" % (self,controlName)
			raise UGenError(msg)
		return self._drive(controlName)

	def __setitem__(self,controlName,val):
		if (controlName not in self._drivable + ["left","right"]):
			msg = "%s[\"%s\"] is not a drivable control for that type of UGen" % (self,controlName)
			raise UGenError(msg)
		setter = self.__getattribute__("_"+controlName+"_setter")
		setter(val)

	#-- special connection syntax for controls --

	def __add__(self,downstream):
		if (not isinstance(downstream,UGen)):
			msg = "cannot connect %s to %s[\"bias\"], %s is not a UGen" % (self,downstream,downstream)
			raise UGenError(msg)
		downstream.bias = self
		return downstream

	def __mul__(self,downstream):
		if (not isinstance(downstream,UGen)):
			msg = "cannot connect %s to %s[\"gain\"], %s is not a UGen" % (self,downstream,downstream)
			raise UGenError(msg)
		downstream.gain = self
		return downstream

	def __mod__(self,downstream):
		# nota bene: even though UGen has no freq attribute, many subclasses
		#            do;  so the special connection syntax for driving freq is
		#            implemented here to keep it with the implementations for
		#            bias and gain
		# $$$ we'd like to check isinstance(downstream,Periodic), but this
		#     .. leads to circular imports
		if (not isinstance(downstream,UGen)):
			msg = "cannot connect %s to %s[\"freq\"], %s is not a Periodic" % (self,downstream,downstream)
			raise UGenError(msg)
		downstream.freq = self
		return downstream

	#-- disconnection syntax --

	def __floordiv__(self,downstream):
		upstream = self
		if (upstream._drives != None): (upstream,_) = upstream._drives
		if (not isinstance(downstream,UGen)):
			msg = "cannot disconnect %s from %s, the latter is not a UGen" % (self,downstream)
			raise UGenError(msg)

		# remove any copies of upstream from downstream's input list
		oldNumFeeds = len(downstream._feeds)
		downstream._feeds = [feed for feed in downstream._feeds if (feed[0] != upstream)]
		connectionsCut = (len(downstream._feeds) != oldNumFeeds)

		# if downstream is a driver and now has no feeds, remove it
		if (downstream._feeds == []) and (downstream._drives != None):
			(customer,controlName) = downstream._drives
			customer._undrive(controlName)

		# remove any copies of upstream from downstream's drivers' input lists
		# (list of ._driven is needed since we're deleting keys inside the loop)
  		for controlName in list(downstream._driven):
			driver = downstream._driven[controlName]
			oldNumFeeds = len(driver._feeds)
			driver._feeds = [feed for feed in driver._feeds if (feed[0] != upstream)]
			if (len(driver._feeds) != oldNumFeeds): connectionsCut = True
			if (driver._feeds == []):
				downstream._undrive(controlName)

		if (not connectionsCut):
			msg = "cannot disconnect %s from %s, there were no connections" % (self,downstream)
			raise UGenError(msg)

 		UGen.pipeline_change()
		return downstream

	#-- add and remove connections --

	def add_feed(self,upstream,fromChannel=None,intoChannel=None):
		downstream = self
		if (hasattr(downstream,"inlet")):
			inlet = downstream.inlet
			if (inlet != None): downstream = inlet

		upOutlets = [upstream]
		if (hasattr(upstream,"outlet")):
			outlet = upstream.outlet
			if   (outlet == None):               pass
			elif (type(outlet) in [list,tuple]): upOutlets =  outlet
			else:                                upOutlets = [outlet]

		if (fromChannel != None) and (intoChannel != None):
			channel = fromChannel + ">" + intoChannel
		elif (fromChannel != None):
			channel = fromChannel + ">"
		elif (intoChannel != None):
			channel = ">" + intoChannel
		else:
			channel = None

		for outlet in upOutlets:
			if (channel == None): feed = (outlet,)
			else:                 feed = (outlet,channel)
			if ("feeds" in UGen.debug):
				if (len(feed) == 1):
					print >>stderr, "add_feed(%s from %s)"      % (downstream,feed[0])
				else:
					print >>stderr, "add_feed(%s from (%s,%s))" % (downstream,feed[0],feed[1])
			downstream._feeds += [feed]

 		UGen.pipeline_change()
 
	def _drive(self,controlName):
		# returns the driver for this control, creating it if not already driven
		if (controlName in self._driven):
			if ("drivables" in UGen.debug):
				print >>stderr, "%s._drive(\"%s\") -> (old) %s" % (self,controlName,self._driven[controlName])
			return self._driven[controlName]

		driver = PassThru(name=self.name+"~"+controlName,channels=1)
		self._driven[controlName] = driver
		controlAttrib = "_" + controlName
		if ("drivables" in UGen.debug): oldControlVal = self.__dict__[controlAttrib]
		self.__dict__[controlAttrib] = driver
		driver._drives = (self,controlName)
		if ("drivables" in UGen.debug):
			print >>stderr, "%s._drive(\"%s\") -> (new) %s"       % (self,controlName,driver)
			print >>stderr, "  %s._driven[\"%s\"]   = %s"         % (self,controlName,self._driven[controlName])
			print >>stderr, "  %s.__dict__[\"%s\"] = %s (was %s)" % (self,controlAttrib,self.__dict__[controlAttrib],oldControlVal)
			print >>stderr, "  %s._drives      = (%s,\"%s\")"     % (driver,self,controlName)

 		UGen.pipeline_change()
		return driver

	def _undrive(self,controlName):
		assert (controlName in self._driven), \
		       "internal error: attempt to _undrive(\"%s\") but _driven=[%s]" \
		     % (controlName,",".join(["\"%s\""%c for c in self._driven]))
		del self._driven[controlName]
		controlAttrib     = "_" + controlName
		controlAttribLast = "_" + controlName + "Last"
		self.__dict__[controlAttrib] = self.__dict__[controlAttribLast]
 		UGen.pipeline_change()

	def dependencies(self):
		return [feed[0] for feed in self._feeds] + self._driven.values()

	#-- left/right connections --

	@property
	def left(self):
		msg = "this type of access to %s.left is not supported" % self
		raise UGenError(msg)

	@left.setter
	def left(self,val):
		self._left_setter(val)

	def _left_setter(self,upstream):
		if (isinstance(upstream,UGen)):
			downstream = UChannel(self,"left")
			downstream.ugen.add_feed(upstream,intoChannel=downstream.channelId)
		else:
			msg = "cannot connect %s to %s.left, the former is not a UGen" % (upstream,self)
			raise UGenError(msg)

	@property
	def right(self):
		msg = "this type of access to %s.right is not supported" % self
		raise UGenError(msg)

	@right.setter
	def right(self,val):
		self._right_setter(val)

	def _right_setter(self,upstream):
		if (isinstance(upstream,UGen)):
			downstream = UChannel(self,"right")
			downstream.ugen.add_feed(upstream,intoChannel=downstream.channelId)
		else:
			msg = "cannot connect %s to %s.right, the former is not a UGen" % (upstream,self)
			raise UGenError(msg)

	#-- drivable bias, no side effects --

	@property
	def bias(self):
		control = self._bias
		if (isinstance(control,UGen)): control = control.last
		self._biasLast = control
		return control

	@bias.setter
	def bias(self,val):
		self._bias_setter(val)

	def _bias_setter(self,val):
		# nota bene: we define separate setter methods for all drivables, to
		#            .. support the use of __getattribute__ in __setitem__
		if (isinstance(val,UGen)):
			self._drive("bias")
			self._bias += val
		else:
			# val is a scalar
			if (isinstance(self._bias,UGen)): del self._driven["bias"]
			self._bias = self._biasLast = float(val)

	#-- drivable gain, no side effects --

	@property
	def gain(self):
		control = self._gain
		if (isinstance(control,UGen)): control = control.last
		self._gainLast = control
		return control

	@gain.setter
	def gain(self,val):
		self._gain_setter(val)

	def _gain_setter(self,val):
		if (isinstance(val,UGen)):
			self._drive("gain")
			self._gain += val
		else:
			# val is a scalar
			if (isinstance(self._gain,UGen)): del self._driven["gain"]
			self._gain = self._gainLast = float(val)

	#-- tick handling --

	def percolate(self):
		feedsNeeded = self._feedsNeeded
		inSample  = [0.0] * feedsNeeded
		inSample2 = [0.0] * feedsNeeded

		# no inputs
		if (self.inChannels == 0):
			self.process_tick()

		# one input channel
		elif (self.inChannels == 1) and (self._feeds == []):
			self.process_tick(self._defaultInSample)
		elif (self.inChannels == 1):
			for (ix,feed) in enumerate(self._feeds):
				if (len(feed) == 1): (feed,channel) = (feed[0],"")
				else:                (feed,channel) =  feed

				sample = 0.0
				if (channel.startswith("L>")):
					sample = feed.last
				elif (channel.startswith("R>")):
					if (feed.outChannels == 2): sample = feed.last2
				elif (feed.outChannels == 1):
					sample = feed.last
				else: # average the two feed outputs as our input
					sample = (feed.last + feed.last2) * halfSqrt2

				if (ix < feedsNeeded-1):
					inSample[ix] =  sample
				else:
					inSample[-1] += sample

			if (feedsNeeded == 1): inSample = inSample[0]
			self.process_tick(inSample)

		# two input channels
		elif (self.inChannels == 2) and (self._feeds == []):
			self.process_tick(self._defaultInSample,self._defaultInSample)
		else: #  (self.inChannels == 2):
			for (ix,feed) in enumerate(self._feeds):
				if (len(feed) == 1): (feed,channel) = (feed[0],"")
				else:                (feed,channel) =  feed

				sample = sample2 = 0.0
				scale  = 1.0
				if (channel.startswith("L>")):
					sample = sample2 = feed.last
					scale  = halfSqrt2
				elif (channel.startswith("R>")):
					if (feed.outChannels == 2):
						sample = sample2 = feed.last2
						scale  = halfSqrt2
				elif (feed.outChannels == 1):
					sample = sample2 = feed.last
					scale  = halfSqrt2
				else:
					sample  = feed.last
					sample2 = feed.last2

				if (channel.endswith(">L")):
					sample2 = 0.0
				elif (channel.endswith(">R")):
					sample = 0.0
				else:
					sample  *= scale
					sample2 *= scale

				if (ix < feedsNeeded-1):
					inSample [ix] =  sample
					inSample2[ix] =  sample2
				else:
					inSample [-1] += sample
					inSample2[-1] += sample2

			if (feedsNeeded == 1):
				inSample  = inSample [0]
				inSample2 = inSample2[0]
			self.process_tick(inSample,inSample2)

		if ("pipeline" in UGen.debug):
			self.report_percolation(self,inSample,inSample2)


	def report_percolation(self,node,inSample,inSample2):
		if (type(inSample)  == list): inSample  = "[%s]" % ",".join([str(x) for x in inSample])
		if (type(inSample2) == list): inSample2 = "[%s]" % ",".join([str(x) for x in inSample2])

		if (node.inChannels == 0):
			if (node.outChannels == 1):
				print >>stderr, "  %s -> %s -> %s"           % ("nothing",node,node.last)
			else:
				print >>stderr, "  %s -> %s -> (%s,%s)"      % ("nothing",node,node.last,node.last2)
		elif (node.inChannels == 1):
			if (node.outChannels == 1):
				print >>stderr, "  %s -> %s -> %s"           % (inSample,node,node.last)
			else:
				print >>stderr, "  %s -> %s -> (%s,%s)"      % (inSample,node,node.last,node.last2)
		else:
			if (node.outChannels == 1):
				print >>stderr, "  (%s,%s) -> %s -> %s"      % (inSample,inSample2,node,node.last)
			else:
				print >>stderr, "  (%s,%s) -> %s -> (%s,%s)" % (inSample,inSample2,node,node.last,node.last2)

	def process_tick(self,sample=None,sample2=None):
		# update any drivables that have an update function
		for controlName in self._driven:
			updateAttrib = "_" + controlName + "_update"
			if (not hasattr(self,updateAttrib)): continue
			updater = self.__getattribute__(updateAttrib)
			driver  = self._driven[controlName]
			if ("drivables" in UGen.debug):
				print >>stderr, "  updating %s._%s from %s (%s)" % (self,controlName,driver,driver.last)
			updater(driver.last)

		# feed the input sample(s) through the tick function
		outSample2 = None
		if (sample == None):
			if (self.outChannels == 2): (outSample,outSample2) = self.tick()
			else:                        outSample             = self.tick()
		elif (sample2 == None):
			if (self.outChannels == 2): (outSample,outSample2) = self.tick(sample)
			else:                        outSample             = self.tick(sample)
		else: # (sample2 != None):
			if (self.outChannels == 1):  outSample             = self.tick(sample,sample2)
			else:                       (outSample,outSample2) = self.tick(sample,sample2)

		# modify the output sample(s) with bias and gain, and save as .last
		if (outSample2 == None):
			self.last = self.bias + self.gain * outSample
			if ("ticks" in UGen.debug):
				print >>stderr, "  process_tick(%s): mono update: %s" \
				              % (self,self.last)
		else: # (outSample2 != None):
			self.last  = self.bias + self.gain * outSample
			self.last2 = self.bias + self.gain * outSample2
			if ("ticks" in UGen.debug):
				print >>stderr, "  process_tick(%s): stereo update: (%s,%s)" \
				              % (self,self.last,self.last2)

	def tick(self,sample,sample2=None):
		if (sample2 == None): return sample
		else:                 return (sample,sample2)


class UChannel(object):
	"""Isolated channel (left/right) for a unit generator.

	These are short-lived objects, used only during parsing to help set up a
	pipeline.
	"""

	id = 0

	#-- construction --

	def __init__(self,ugen,channel):
		self.id = UChannel.id
		self.name    = "%s.%s" % (ugen.name,self.id)
		self.ugen    = ugen
		self.channel = channel
		if   (channel == "left"):  self.channelId = "L"
		elif (channel == "right"): self.channelId = "R"
		else: raise ValueError("invalid UChannel channel \"%s\"" % channel)

	#-- identification --

	def __str__(self):
		return "%s:%s" % (self.id,self.name)

	#-- connection syntax --

	def __rshift__(self,downstream):
		if ("feeds" in UGen.debug): print >>stderr, "__rshift__(%s,%s)" % (self,downstream)
		if (type(downstream) in (list,tuple)):
			for element in downstream: self >> element
			return downstream

		upstream = self.ugen
		if (upstream._drives != None): (upstream,_) = upstream._drives
		if (isinstance(downstream,UChannel)):
			downstream.ugen.add_feed(upstream,fromChannel=self.channelId,intoChannel=downstream.channelId)
			return downstream
		if (isinstance(downstream,UGen)):
			downstream.add_feed(upstream,fromChannel=self.channelId)
			return downstream
		msg = "cannot connect %s to %s, the latter is not a UGen" % (upstream,downstream)
		raise UGenError(msg)

	def __iadd__(self,upstream):
		if (type(upstream) in (list,tuple)):
			for element in upstream: self += element
			# $$$ problem, fix this
			return self

		if (not isinstance(upstream,UGen)):
			msg = "cannot connect %s to %s, the former is not a UGen" % (upstream,self)
			raise UGenError(msg)
		if (upstream._drives != None):
			msg = "cannot connect %s to %s, the former is an internal UGen" % (upstream,self)
			raise UGenError(msg)

		downstream = self.ugen
		channelId  = self.channelId
		if ("+connection" in UGen.debug):
			print >>stderr, "%s += (%s,>%s)" % (downstream,upstream,channelId)
		downstream.add_feed(upstream,intoChannel=channelId)
		# $$$ problem, fix this
		return self


class UGraph(UGen):
	"""Parent class for connection-graph ugens.

	Subclasses should define self.inlet and/or self.outlet and create unit
	generators to connect inlet to outlet.

	self.inlet is a single ugen.  If the subclass has no input feeds it need
	not define an inlet.

	self.outlet can be a single ugen or a list of ugens.  If the subclass has
	no outputs it need not define an inlet.
	"""
	# $$$ need to test/handle the notion of drivable controls for a UGraph

	def __init__(self,name=None):
		super(UGraph,self).__init__(name=name)
		if ("constructors" in UGen.debug): print >>stderr, "UGraph.__init__(%s)" % name


class PassThru(UGen):
	"""Parent class for pass-thru ugens.

	This class has three typical uses.  First, it can serve as a master
	collection point for a group of chains, providing a convenient point to
	apply a collective gain.

	Similarly, this is the ugen created when one ugen or a chain is used to
	drive another ugen's control (e.g. frequency).  A PassThru object is
	instantiated to make this connection, usually behind the scenes.

	Finally, it acts as a base class for classes that have non-pipeline
	side effects, such as TextOut and WavOut.
	"""

	def __init__(self,channels=1,name=None,
		         bias=0.0,gain=1.0):
		super(PassThru,self).__init__(inChannels=channels,outChannels=channels,name=name,
		                              bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "PassThru.__init__(%s)" % name
		if (self.inChannels != self.outChannels):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)


class Mixer(PassThru):
	"""Class to mix two signals.

	This class will typically have two input feeds (not to be confused with
	channels, which are a different entity).  The first feed is controlled by
	the "dry" setting, and the second is controlled by the "wet" setting.

	If there is only one feed the second feed is treated as silent.  If there
	are more than two feeds all but the first are summed to form the wet feed.
	"""

	def __init__(self,channels=1,name=None,
		         bias=0.0,gain=1.0,dry=None,wet=None):
		super(Mixer,self).__init__(channels=channels,name=name,
		                           bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "Mixer.__init__(%s)" % name
		if (self.inChannels != self.outChannels):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
			    % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		self._feedsNeeded = 2

		self._drivable += ["dry","wet"]
		self._dry = self._dryLast = 0.0  # overwritten by self.dry = dry
		self._wet = self._wetLast = 0.0  # overwritten by self.wet = wet
		if (dry == None): dry = 1.0
		if (wet == None): wet = 0.0
		self.dry = dry
		self.wet = wet

	#-- drivable dry, no side effects --

	@property
	def dry(self):
		control = self._dry
		if (isinstance(control,UGen)): control = control.last
		self._dryLast = control
		return control

	@dry.setter
	def dry(self,val):
		self._dry_setter(val)

	def _dry_setter(self,val):
		if (isinstance(val,UGen)):
			self._drive("dry")
			self._dry += val
		else:
			# val is a scalar
			if (isinstance(self._dry,UGen)): del self._driven["dry"]
			self._dry = self._dryLast = float(val)

	#-- drivable wet, no side effects --

	@property
	def wet(self):
		control = self._wet
		if (isinstance(control,UGen)): control = control.last
		self._wetLast = control
		return control

	@wet.setter
	def wet(self,val):
		self._wet_setter(val)

	def _wet_setter(self,val):
		if (isinstance(val,UGen)):
			self._drive("wet")
			self._wet += val
		else:
			# val is a scalar
			if (isinstance(self._wet,UGen)): del self._driven["wet"]
			self._wet = self._wetLast = float(val)

	#-- tick handling --

	def tick(self,samples,samples2=None):
		if (samples2 == None):
			return  self.dry*samples [0] + self.wet*samples [1]
		else:
			return (self.dry*samples [0] + self.wet*samples [1],
			        self.dry*samples2[0] + self.wet*samples2[1])


class Pan(UGen):
	"""Class to expand a mono input to a stereo output.

	The pan control, wich is drivable, is clipped to the range -1 <= pan <= +1.
	-1 will place the output on the left channel, +1 will place it on the right
	channel.
	"""
	# $$$ check whether sin/cos formulation is "correct"
	# $$$ allow caller to set the functions that map pan pos to a L/R pair

	def __init__(self,name=None,
	             bias=None,gain=None,pan=None):
		super(Pan,self).__init__(inChannels=1,outChannels=2,name=name,
		                         bias=bias,gain=gain)
		if ("constructors" in UGen.debug): print >>stderr, "Pan.__init__(%s)" % name
		if (self.inChannels != 1) or (self.outChannels != 2):
			msg = "inChannels=%s with outChannels=%s is not valid for %s" \
		        % (self.inChannels,self.outChannels,self)
			raise UGenError(msg)

		self._drivable += ["pan"]
		self._pan = self._panLast = 0.0  # overwritten by self.pan = pan
		if (pan == None): pan = UGen.defaultPan
		self.pan = pan

	#-- drivable pan, with side effects --

	@property
	def pan(self):
		control = self._pan
		if (isinstance(control,UGen)):
			control = control.last
		if (control != self._panLast):
			self._pan_update(control)
		return control

	@pan.setter
	def pan(self,val):
		self._pan_setter(val)

	def _pan_setter(self,val):
		if (isinstance(val,UGen)):
			self._drive("pan")
			self._pan += val
		else:
			# val is a scalar
			if (isinstance(self._pan,UGen)): del self._driven["pan"]
			self._pan_update(val)

	def _pan_update(self,val):
		self._pan = self._panLast = val = clip_value(float(val),-1.0,1.0)
		# side effects
		p = quarterPi * (val+1.0)
		self._panLeft  = cos(p)
		self._panRight = sin(p)
		if ("pan drive" in UGen.debug):
			print >>stderr, "  %s._pan_update(%s) -> panLeft=%s panRight=%s" \
		                  % (self,val,self._panLeft,self._panRight)

	#-- tick handling --

	def tick(self,sample):
		return (sample*self._panLeft,sample*self._panRight)
