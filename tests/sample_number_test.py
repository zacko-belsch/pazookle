#!/usr/bin/env python
"""
sample_number_test

Test clock management to make certain that a yield of, e.g., 100 generates
exactly 100 samples.
"""

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,console,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import SinOsc
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --samples=<samples>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug

	# parse the command line

	duration = 100
	debug    = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("N=")) or (arg.startswith("--samples=")):
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

	zook.spork(sample_number_test(duration))
	zook.run()


def sample_number_test(duration):
	a = SinOsc(gain=1,freq=440)
	a >> console
	yield duration


if __name__ == "__main__": main()
