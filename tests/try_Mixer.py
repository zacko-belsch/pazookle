#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,Shreduler
from pazookle.ugen     import UGen,Mixer
from pazookle.generate import SinOsc
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --freq1=<value>       set the first frequency
  --freq2=<value>       set the second frequency
  --dry=<value>         set dry level (mix for second oscillator)
  --wet=<value>         set wet level (mix for second oscillator)
  --channels=<1|2>      number of output channels
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global freq1,freq2,dry,wet,numChannels

	# parse the command line

	freq1       = 440.0
	freq2       = 660.0
	dry         = 0.5
	wet         = 0.2
	numChannels = 1
	duration    = 3.0
	debug       = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("F1=")) or (arg.startswith("--freq1=")) or (arg.startswith("--frequency1=")):
			freq1 = float_or_fraction(argVal)
		elif (arg.startswith("F2=")) or (arg.startswith("--freq2=")) or (arg.startswith("--frequency2=")):
			freq2 = float_or_fraction(argVal)
		elif (arg.startswith("D=")) or (arg.startswith("--dry=")):
			dry = float_or_fraction(argVal)
		elif (arg.startswith("W=")) or (arg.startswith("--wet=")):
			wet = float_or_fraction(argVal)
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

	zook.spork(mixer_test(duration*zook.sec))
	zook.run()


def mixer_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=numChannels)

	osc1 = SinOsc(gain=1.0,freq=freq1)
	osc2 = SinOsc(gain=1.0,freq=freq2)
	mixer = Mixer(dry=dry,wet=wet,channels=numChannels)

	osc1 >> mixer >> output
	osc2 >> mixer

	yield duration
	output.close()


if __name__ == "__main__": main()
