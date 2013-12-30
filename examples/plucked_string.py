#!/usr/bin/env python
"""
plucked_string

Demonstrate a "plucked string" sound, based on the Karplus-Strong scheme.  This
follows example 6.9 from "Programming for Musicians and Digital Artists" by
Kapur, Cook, Salazar and Wang.
"""

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from random            import seed as random_seed,randint
from pazookle.shred    import zook,now,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import Noise
from pazookle.envelope import ADSR
from pazookle.filter   import OneZero
from pazookle.buffer   import Delay
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --seed=<string>       random number generator seed
  --noise=<string>      random number generator seed for noise generator
  --gain=<value>        set the gain
  --pluck=<msec>        set the time from one pluck to the next
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global noiseSeed,gain,pluckTime

	# parse the command line

	noiseSeed  = None
	gain       = 1.0
	pluckTime  = 300 * zook.msec
	duration   = 10.0
	debug      = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("--seed=")):
			random_seed(argVal)
		elif (arg.startswith("--noise=")):
			noiseSeed = float_or_fraction(argVal)
		elif (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("Q=")) or (arg.startswith("--pluck=")):
			pluckTime = float_or_fraction(argVal) * zook.msec
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

	zook.spork(plucked_string(duration*zook.sec))
	zook.run()


def plucked_string(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=1)

	# create the sound chain;  we use a noise generator with an attack-decay
	# envelope (no sustain and thus no release);  this is fed through a
	# "string" delay with low-pass-filtered feedback

	nosey   = Noise(seed=noiseSeed,gain=gain)
	pluck   = ADSR(adsr=(2*zook.msec,2*zook.msec,0,0))
	string  = Delay()
	lowPass = OneZero()

	nosey >> pluck >> string >> output
	string >> lowPass >> string

	# generate a series of random notes

	startTime = now()
	while (now() < startTime + duration):
		string.delay = delay = randint(110,440)
		print "T=%.3f delay=%d" % (now()/zook.sec,delay)
		pluck.key_on()
		yield pluckTime


if __name__ == "__main__": main()
