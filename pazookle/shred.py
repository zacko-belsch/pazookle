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

import os.path
from sys    import stderr
from types  import GeneratorType
from ugen   import UGen
from output import TextOut


class ShredulerError(Exception):
	def __init__(self,message):
		Exception.__init__(self,message)


class Shreduler(object):
	"""Manage audio shreds.

	Debug settings as of this writing:
		shreds:        shred activation
		pipeline:      values percolating through the pipeline

	Nota bene: self.clock is an integer that counts by one with each sample.
	           self.now   is a floating point value, now >= clock, which
	                      .. ideally is such that floor(now) == clock;  when
	                      .. floor(now) > clock we generate one sample and
	                      .. increment clock
	"""
	# $$$ modify shred protocol so that a shred can return a list or tuple
	#     .. containing no more than one time;  the other entries will all be
	#     .. event or message objects;  the idea is that the shred will wait
	#     .. for the earliest event yielded (or the time if it expires first);
	#     .. the probem though is that we have no way to communicate to the
	#     .. shred *which* event has triggered

	id = 0
	debug = {}

	@staticmethod
	def set_debug(debugNames):
		if (type(debugNames) not in (list,tuple)): debugNames = [debugNames]
		for debugName in debugNames: Shreduler.debug[debugName] = True

	@staticmethod
	def unset_debug(debugNames):
		if (type(debugNames) not in (list,tuple)): debugNames = [debugNames]
		for debugName in debugNames:
			try: del Shreduler.debug[debugName]
			except KeyError: pass

	#-- construction --

	def __init__(self,sinks=None,samplingRate=44100):
		if (sinks == None): self.sinks = []
		else:               self.sinks = sinks
		self.samplingRate = samplingRate
		self.set_times()
		self._shreds = []
		self._lastYield      = {}    # maps shred id to (time,duration) of last yield
		self._updateOrder    = None
		self._pipelineChange = False
		self._clock = 0
		self._now   = 0.0

	def set_times(self):
		self.msec = self.samplingRate / 1000.0
		self.sec  = float(self.samplingRate)
		self.min  = self.samplingRate * 60.0
		self.hour = self.samplingRate * 3600.0

	#-- attribute access (by intent, these are NOT properties) --

	def clock(self):
		return self._clock

	def now(self):
		return self._now

	#-- shred scheduling --

	def spork(self,shredFunction,shredName=None):
		# $$$ keep a dict that maps id to (name,function), to be used for
		#     .. operations like kill_shred() and yield ("shred finished",shredId)
		if (not isinstance(shredFunction,GeneratorType)):
			if (shredName == None): shredName = "(unnamed)"
			msg = "shred \"%s\" is invalid, it's not a python generator" % shredName
			raise ShredulerError(msg)
		Shreduler.id += 1
		shredId = Shreduler.id
		if (shredName == None): shredName = shredFunction.__name__
		shredName = "%s.%s" % (shredName,shredId)
		self._lastYield[shredId] = (None,None)
		self.insert_shred(None,shredId,shredFunction,shredName)
		return shredId

	def run(self):
		while (self._shreds != []):
			self.run_earliest_shred()

	def run_earliest_shred(self):
		(when,shredId,shredFunction,shredName) = self._shreds.pop(0)
		if (when != None):
			while (self._clock+1 <= when):
				self.run_sample_pipe()

		if ("shreds" in Shreduler.debug):
			print >>stderr, "running %s" % shredName
		try:
			if (when == None): self._now = self._clock
			else:              self._now = when
			when = shredFunction.next()
			if ("shreds" in Shreduler.debug):
				if (type(when) == tuple):
					print >>stderr, "%s yielded (%s)" % (shredName,",".join([str(x) for x in when]))
				else:
					print >>stderr, "%s yielded %s" % (shredName,when)
		except StopIteration:
			if ("shreds" in Shreduler.debug):
				print >>stderr, "%s has completed" % shredName
			del self._lastYield[shredId]
			return

		if (type(when) != tuple):
			if (when != None): when += self._now
		elif (when[0] == "absolute") and (len(when) == 2):
			(_,when) = when
		else:
			msg = "incomprehensible yield from shred \"%s\": (%s)" % (shredName,",".join([str(x) for x in when]))
			raise ShredulerError(msg)

		if (when == None) or (when < self._now):
			msg = "shred \"%s\" yielded %s <= %s" % (shredName,when,self._now)
			raise ShredulerError(msg)

		if (when == self._now) and (self._lastYield[shredId] == (when,0)):
			msg = "shred \"%s\" yielded without advancing time twice in a row (now=%s)" \
			    % (shredName,when)
			raise ShredulerError(msg)

		(lastWhen,_) = self._lastYield[shredId]
		if (lastWhen == None): duration = 0
		else:                  duration = when - lastWhen
		self._lastYield[shredId] = (when,duration)
		self.insert_shred(when,shredId,shredFunction,shredName)

	def insert_shred(self,when,shredId,shredFunction,shredName):
		# $$$ replace this with a priority queue implementation
		# insert new shred before any that are waiting for a later time
		insertIx = len(self._shreds)
		if (when == None):
			for (ix,(oldWhen,_,_,_)) in enumerate(self._shreds):
				if (oldWhen == None): continue
				insertIx = ix
				break
		else:
			for (ix,(oldWhen,_,_,_)) in enumerate(self._shreds):
				if (oldWhen <= when): continue
				insertIx = ix
				break
		self._shreds.insert(insertIx,(when,shredId,shredFunction,shredName))

	#-- pipline construction --

	def add_sink(self,sink):
		if (sink not in self.sinks):
			self.sinks += [sink]
			self.pipeline_change()

	def remove_sink(self,sink):
		if (sink in self.sinks):
			self.sinks.remove(sink)
			self.pipeline_change()

	def pipeline_change(self):
		self._pipelineChange = True

	def find_update_order(self):
		# the algorithm here is based on the depth-first search topological
		# sorting algorithm at en.wikipedia.org/wiki/Topological_sorting
		# the main modification is that when we encounter a cycle, we simply
		# ignore that link rather than abort the process
		assert (self.sinks != []), \
		       "internal error: find_update_order caled with no sinks" \
		     % numFuncs
		self._order = []
		self._markedNodes = {}
		for node in self.sinks:
			if (node.id in self._markedNodes): continue
			if (node.ignoreInputlessSink):
				# if a sink has no input, and it's not generative, ignore it
				if (node.dependencies() == []): continue
			self.visit(node)
		order = list(self._order)
		del self._order
		del self._markedNodes
		return order

	def visit(self,node):
		if (node.id in self._markedNodes): return
		self._markedNodes[node.id] = True
		for predecessor in node.dependencies():
			self.visit(predecessor)
		self._order += [node]

	#-- pipline percolation --

	def run_sample_pipe(self):
		self._clock += 1
		if ("pipeline" in Shreduler.debug):
			print >>stderr, "\n=== generating sample #%s ===" % self._clock
		elif ("progress" in Shreduler.debug):
			if (self._clock % 1000 == 0):
				print >>stderr, "=== generating sample #%s ===" % self._clock
		if (self.sinks == []):
			if ("pipeline" in Shreduler.debug):
				print >>stderr, "(pipeline has no sinks, so no percolation)"
			return
		if (self._pipelineChange):
			self._updateOrder    = None
			self._pipelineChange = False
		if (self._updateOrder == None):
			self._updateOrder = self.find_update_order()
			if ("pipeline" in Shreduler.debug):
				print >>stderr, "update order: [%s]" % ",".join([str(node) for node in self._updateOrder])

		for node in self._updateOrder:
			node.percolate()


# initialization

console  = TextOut(name="console", channels=1)
console2 = TextOut(name="console2",channels=2)

zook = Shreduler(sinks=[console,console2],samplingRate=44100)
now  = zook.now
UGen.set_shreduler(zook)

zookPath       = os.path.dirname(os.path.realpath(__file__))
zookParentPath = os.path.abspath(os.path.join(zookPath,os.path.pardir))
zookClipsPath  = os.path.join(zookParentPath,"clips")

