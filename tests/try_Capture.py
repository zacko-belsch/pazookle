#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import Noise
from pazookle.filter   import LowPass
from pazookle.buffer   import Capture,Clip
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --seed=<string>       random number generator seed
  --gain=<value>        set the gain
  --freq=<value>        set the cutoff frequency
  Q=<value>             set the filter's Q value
  --channels=<1|2>      number of output channels
  --capture=<seconds>   length of caotured sample
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global seed,gain,freq,Q,numChannels

	# parse the command line

	seed        = None
	gain        = 1.0
	freq        = 400.0
	Q           = 7.0
	numChannels = 1
	capDuration = 1.0 / 440
	duration    = 5.0
	debug       = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("--seed=")):
			seed = argVal
		elif (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("F=")) or (arg.startswith("--freq=")) or (arg.startswith("--frequency=")):
			freq = float_or_fraction(argVal)
		elif (arg.startswith("Q=")):
			Q = float_or_fraction(argVal)
		elif (arg.startswith("--channels=")):
			numChannels = int(argVal)
		elif (arg.startswith("C=")) or (arg.startswith("--cap=")) or (arg.startswith("--capture=")):
			duration = float_or_fraction(argVal)
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

	zook.spork(capture_test(capDuration*zook.sec,duration*zook.sec))
	zook.run()


def capture_test(capDuration,duration):

	# set up a sound cahin and capture its output

	nosey = Noise(seed=seed,outChannels=numChannels)
	nosey.gain = 1
	phil = LowPass(freq=freq,Q=Q)
	phil.gain = 1.0
	cap = Capture()

	nosey >> phil >> cap
	yield capDuration

	loopData = cap.buffer()

	# disable that sound chain;  note that turning off capture removes the
	# capture object from the list of sinks, and thus none of its inputs will
	# be updated in the new pipeline

	cap.off()

	# set up a loop and capture it to a file

	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=numChannels)

	clip = Clip(source=loopData,gain=gain,loop=True)
	clip.trigger()

	clip >> output
	yield duration
	output.close()


if __name__ == "__main__": main()
