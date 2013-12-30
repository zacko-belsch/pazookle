#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,Shreduler
from pazookle.ugen     import UGen,Pan
from pazookle.generate import SinOsc
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --phase=<value>       set the phase
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global phase

	# parse the command line

	phase    = 0.75
	duration = 10.0
	debug    = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("P=")) or (arg.startswith("--phase=")):
			phase = float_or_fraction(argVal)
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

	zook.spork(pan_test(duration*zook.sec))
	zook.run()


def pan_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=2)

	panContol = SinOsc()
	panContol.gain  = 1.0
	panContol.freq  = 0.5
	panContol.phase = phase * panContol.cycleScale

	panhandler = Pan()
	panhandler.gain = 1.0

	oscar = SinOsc()
	oscar.gain = 0.6
	oscar.freq = 441.0

	oscar >> panhandler >> output
	panhandler.pan = panContol

	if ("transcripts" in debug):
		print >>stderr
		print >>stderr, "=== transcripts ==="
		print >>stderr, oscar.transcript          (extra=["class"])
		print >>stderr, panContol.transcript      (extra=["class"])
		print >>stderr, panhandler.transcript     (extra=["class"])
		print >>stderr, panhandler._pan.transcript(extra=["class"])

	yield duration
	output.close()


if __name__ == "__main__": main()
