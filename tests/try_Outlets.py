#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,Shreduler
from pazookle.ugen     import UGen,UGraph
from pazookle.generate import SinOsc,SawOsc,TriOsc,SqrOsc
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  <osc class>            one of SinOsc,SawOsc,TriOsc,SqrOsc
  --gain=<value>         set the gain
  --freq=<value>         set the root frequency
  --harmonics=<weights>  weights for each harmonic (comma-separated list)
  --duration=<seconds>   length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global oscType,gain,freq,harmonics

	# parse the command line

	oscType   = SinOsc
	gain      = 0.5
	freq      = 440.0
	harmonics = [1,.8,.6,.4,.2]
	duration  = 3.0
	debug     = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg == "SinOsc"):
			oscType = SinOsc
		elif (arg == "SawOsc"):
			oscType = SawOsc
		elif (arg == "TriOsc"):
			oscType = TriOsc
		elif (arg == "SqrOsc"):
			oscType = SqrOsc
		elif (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("F=")) or (arg.startswith("--freq=")) or (arg.startswith("--frequency=")):
			freq = float_or_fraction(argVal)
		elif (arg.startswith("--harm=")) or (arg.startswith("--harmonics=")):
			harmonics = [float_or_fraction(w) for w in argVal.split(",")]
		elif (arg.startswith("T=")) or (arg.startswith("--dur=")) or (arg.startswith("--duration=")):
			duration = float_or_fraction(argVal)
		elif (arg == "--help"):
			usage()
		elif (arg.startswith("--debug=")):
			debug += argVal.split(",")
		elif (arg.startswith("--")):
			usage("unrecognized option: %s" % arg)
		else:
			usage("unrecognized option: %s" % arg)

	# run the test

	UGen.set_debug(debug)
	Shreduler.set_debug(debug)

	zook.spork(outlets_test(duration*zook.sec))
	zook.run()


def outlets_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=1)

	syn = AdditiveSynth(gain=gain,freq=freq,
	                    harmonics=harmonics,oscType=oscType)

	syn >> output

	if ("transcripts" in debug):
		print >>stderr
		print >>stderr, "=== transcripts ==="
		for component in syn.outlet:
			print >>stderr, component.transcript (extra=["class"])
		print >>stderr, output.transcript (extra=["class"])

	yield duration
	output.close()


class AdditiveSynth(UGraph):
	"""Example of a graph with outlets only."""

	def __init__(self,name=None,
	             gain=None,freq=None,phase=None,
	             harmonics=None,oscType=None):
		super(AdditiveSynth,self).__init__(name=name)

		if (gain      == None): gain      = 1.0
		if (freq      == None): freq      = UGen.defaultFreq
		if (phase     == None): phase     = UGen.defaultPhase
		if (harmonics == None): harmonics = [1,.5,.25]
		if (oscType   == None): oscType   = SinOsc

		gain /= float(sum([abs(w) for w in harmonics]))

		self.outlet = []
		for (ix,weight) in enumerate(harmonics):
			if (weight == 0): continue
			harmonic = ix+1
			component = oscType(gain=gain*weight,freq=freq*harmonic)
			self.outlet += [component]


if __name__ == "__main__": main()

