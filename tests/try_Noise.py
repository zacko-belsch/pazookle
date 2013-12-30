#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import Noise
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction

def usage(s=None):
	message = """
usage: %s [options]
  --seed=<string>       random number generator seed
  --subsample=<number>  subsample the random number generator output
  --channels=<1|2>      number of output channels
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global seed,subsample,numChannels

	# parse the command line

	seed        = None
	subsample   = None
	numChannels = 1
	duration    = 5.0
	debug       = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("--seed=")):
			seed = argVal
		elif (arg.startswith("--subsample=")):
			subsample = float_or_fraction(argVal)
		elif (arg.startswith("--channels=")):
			numChannels = int(argVal)
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

	zook.spork(noise_test(duration*zook.sec))
	zook.run()


def noise_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=numChannels)

	nosey = Noise(seed=seed,outChannels=numChannels,subsample=subsample)
	nosey.gain = 1.0

	nosey >> output

	yield duration
	output.close()


if __name__ == "__main__": main()
