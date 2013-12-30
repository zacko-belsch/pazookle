#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import SinOsc
from pazookle.envelope import LinearRamp,CubicRamp
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  <ramp class>          one of LinearRamp,CubicRamp
  --gain=<value,value>  set the gain (start and end)
  --modfreq=<value>     set the first frequency
  --carfreq=<value>     set the second frequency
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global rampType,modGainStart,modGainEnd,modFreq,carFreq,specialSyntax

	# parse the command line

	rampType      = LinearRamp
	modGainStart  = 10.0
	modGainEnd    = 2500.0
	modFreq       = 33.0
	carFreq       = 383.0
	duration      = 10.0
	specialSyntax = False
	debug         = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg == "LinearRamp"):
			rampType = LinearRamp
		elif (arg == "CubicRamp"):
			rampType = CubicRamp
		elif (arg.startswith("G=")) or (arg.startswith("--gain=")):
			(modGainStart,modGainEnd) = argVal.split(",")
			modGainStart = float_or_fraction(modGainStart)
			modGainEnd   = float_or_fraction(modGainEnd)
		elif (arg.startswith("FM=")) or (arg.startswith("--modfreq=")):
			modFreq = float_or_fraction(argVal)
		elif (arg.startswith("FC=")) or (arg.startswith("--carfreq=")):
			carFreq = float_or_fraction(argVal)
		elif (arg.startswith("T=")) or (arg.startswith("--dur=")) or (arg.startswith("--duration=")):
			duration = float_or_fraction(argVal)
		elif (arg == "--special"):
			specialSyntax = True
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

	zook.spork(fm_test(duration*zook.sec))
	zook.run()


def fm_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=1)

	ramp      = rampType(bias=modGainStart,
	                     gain=modGainEnd-modGainStart)
	fmMod     = SinOsc  (bias=carFreq,
	                     gain=ramp,
	                     freq=modFreq)
	fmCarrier = SinOsc  (gain=0.3)

	if (specialSyntax):
		fmMod % fmCarrier >> output
	else:
		fmMod >> fmCarrier["freq"] >> output

	ramp.trigger(1.0,duration)
	yield duration
	output.close()


if __name__ == "__main__": main()
