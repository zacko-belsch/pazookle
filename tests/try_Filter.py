#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import Noise
from pazookle.filter   import LowPass,HighPass,BandPass,BandReject
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --seed=<string>       random number generator seed
  --subsample=<number>  subsample the random number generator output
  <filter class>        one of LowPass,HighPass,BandPass,BandReject
  --gain=<value>        set the gain
  --freq=<value>        set the cutoff frequency
  Q=<value>             set the filter's Q value
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global seed,subsample,filtType,gain,freq,Q

	# parse the command line

	seed      = None
	subsample = None
	filtType  = LowPass
	gain      = 1.0
	freq      = 400.0
	Q         = 7.0
	duration  = 3.0
	debug     = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("--seed=")):
			seed = argVal
		elif (arg.startswith("--subsample=")):
			subsample = float_or_fraction(argVal)
		elif (arg == "LowPass"):
			filtType = LowPass
		elif (arg == "HighPass"):
			filtType = HighPass
		elif (arg == "BandPass"):
			filtType = BandPass
		elif (arg == "BandReject"):
			filtType = BandReject
		elif (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("F=")) or (arg.startswith("--freq=")) or (arg.startswith("--frequency=")):
			freq = float_or_fraction(argVal)
		elif (arg.startswith("Q=")):
			Q = float_or_fraction(argVal)
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

	zook.spork(filter_test(duration*zook.sec))
	zook.run()


def filter_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=1)

	nosey = Noise(seed=seed,outChannels=1,subsample=subsample)
	nosey.gain = gain

	# $$$ freq and Q should be drivable; when they are, add LFO's to drive them
	phil = filtType(freq=freq,Q=Q)
	phil.gain = 1.0

	nosey >> phil >> output

	yield duration
	output.close()


if __name__ == "__main__": main()
