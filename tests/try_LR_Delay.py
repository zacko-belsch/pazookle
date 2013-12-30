#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,Shreduler
from pazookle.ugen     import UGen,PassThru
from pazookle.buffer   import Delay
from pazookle.generate import SinOsc,TriOsc
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --gain=<value>        set the gain
  --freq1=<value>       set the left channel frequency
  --freq2=<value>       set the right channel frequency
  --delay1=<value>      set the left channel delay
  --delay2=<value>      set the right channel delay
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global gain,freq1,freq2,delay1,delay2

	# parse the command line

	gain      = 0.5
	freq1     = 440.0
	freq2     = 660.0
	delay1    = 100 * zook.msec
	delay2    = 200 * zook.msec
	duration  = 3.0
	debug     = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("F1=")) or (arg.startswith("--freq1=")) or (arg.startswith("--frequency1=")):
			freq1 = float_or_fraction(argVal)
		elif (arg.startswith("F2=")) or (arg.startswith("--freq2=")) or (arg.startswith("--frequency2=")):
			freq2 = float_or_fraction(argVal)
		elif (arg.startswith("D1=")) or (arg.startswith("--delay1=")):
			delay1 = float_or_fraction(argVal)
		elif (arg.startswith("D2=")) or (arg.startswith("--delay2=")):
			delay2 = float_or_fraction(argVal)
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

	zook.spork(delay_LR_test(duration*zook.sec))
	zook.run()


def delay_LR_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=2)

	lft = SinOsc(gain=gain,freq=freq1)
	rgt = TriOsc(gain=gain,freq=freq2)
	master = PassThru(channels=2)

	del1 = del2 = None
	if (delay1 > 0): del1 = Delay(delay=delay1)
	if (delay2 > 0): del2 = Delay(delay=delay2)

	if (del1 == None): lft         >> master["left"]
	else:              lft >> del1 >> master["left"]
	if (del2 == None): rgt         >> master["right"]
	else:              rgt >> del2 >> master["right"]

	master >> output

	if ("transcripts" in debug):
		print >>stderr
		print >>stderr, "=== transcripts ==="
		print >>stderr, lft.transcript (extra=["class"])
		print >>stderr, rgt.transcript (extra=["class"])
		if (del1 != None): print >>stderr, del1.transcript(extra=["class"])
		if (del2 != None): print >>stderr, del2.transcript(extra=["class"])
		print >>stderr, master.transcript (extra=["class"])
		print >>stderr, output.transcript (extra=["class"])

	yield duration
	output.close()


if __name__ == "__main__": main()
