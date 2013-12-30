#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,Shreduler
from pazookle.ugen     import UGen
from pazookle.buffer   import Delay
from pazookle.generate import SinOsc
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --gain=<value>        set the gain
  --freq=<value>        set the frequency
  --channels=<1|2>      number of output channels
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global gain,freq,delay,numChannels

	# parse the command line

	gain        = 0.5
	freq        = 440.0
	delay       = 100 * zook.msec
	numChannels = 1
	duration    = 3.0
	debug       = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("F=")) or (arg.startswith("--freq=")) or (arg.startswith("--frequency=")):
			freq = float_or_fraction(argVal)
		elif (arg.startswith("D=")) or (arg.startswith("--delay=")):
			delay = float_or_fraction(argVal) * zook.msec
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

	zook.spork(delay_test(duration*zook.sec))
	zook.run()


def delay_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=numChannels)

	o = SinOsc(gain=gain,freq=freq)
	d = Delay(delay=delay,channels=numChannels)
	o >> d >> output

	yield duration
	output.close()


if __name__ == "__main__": main()
