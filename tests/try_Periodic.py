#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,console,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import Periodic,SinOsc,SawOsc,TriOsc,SqrOsc,ImpulseTrain
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  <osc class>           one of SinOsc,SawOsc,TriOsc,SqrOsc,ImpulseTrain
  --bias=<value>        set the bias
  --gain=<value>        set the gain
  --freq=<value>        set the frequency
  --phase=<value>       set the phase
  --duration=<seconds>  length of the test
  --wav=<filename>      write the output to a .wav file""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global oscType,bias,gain,freq,phase
	global filename

	# parse the command line

	oscType   = Periodic
	bias      = 0.0
	gain      = 0.5
	freq      = 440.0
	phase     = 0.0
	duration  = 1.0
	filename  = None
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
		elif (arg == "ImpulseTrain"):
			oscType = ImpulseTrain
		elif (arg.startswith("B=")) or (arg.startswith("--bias=")):
			bias = float_or_fraction(argVal)
		elif (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("F=")) or (arg.startswith("--freq=")) or (arg.startswith("--frequency=")):
			freq = float_or_fraction(argVal)
		elif (arg.startswith("P=")) or (arg.startswith("--phase=")):
			phase = float_or_fraction(argVal)
		elif (arg.startswith("T=")) or (arg.startswith("--dur=")) or (arg.startswith("--duration=")):
			duration = float_or_fraction(argVal)
		elif (arg.startswith("--wav=")):
			filename = argVal
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

	zook.spork(periodic_test(duration*zook.sec))
	zook.run()


def periodic_test(duration):
	output = console
	if (filename != None):
		print >>stderr, "writing audio output to %s" % filename
		wavOut = WavOut(filename=filename,channels=1)
		output = wavOut

	a = oscType(bias=bias,gain=gain,freq=freq)
	if (oscType != ImpulseTrain): a.phase = phase

	a >> output
	yield duration
	output.close()


if __name__ == "__main__": main()
