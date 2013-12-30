#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys             import argv,stdin,stderr,exit
from random          import randint,random as unit_random
from pazookle.shred  import zook,zookClipsPath,Shreduler
from pazookle.ugen   import UGen
from pazookle.buffer import Clip
from pazookle.output import WavOut
from pazookle.parse  import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --gain=<value>        set the gain
  --loop[=<rate>]       play the clip as a loop
  --path=<filename>     set the path to read the clip from
  --in=<filename>       read the clip from a .wav file
  --duration=<seconds>  length of the test (only meaningful for loop test)""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global gain,loopRate,clipPath,clipFilename

	# parse the command line

	gain         = 0.5
	loopRate     = None
	clipPath     = zookClipsPath
	clipFilename = "chucka.wav"
	duration     = 5.0
	debug        = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg == "--loop"):
			loopRate = 1.0
		elif (arg.startswith("--loop=")):
			loopRate = float_or_fraction(argVal)
		elif (arg.startswith("--path=")):
			clipPath = argVal
		elif (arg.startswith("--in=")) or (arg.startswith("--clip=")):
			clipFilename = argVal
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

	if (loopRate != None): zook.spork(loop_test(duration*zook.sec))
	else:                  zook.spork(clip_test())
	zook.run()


def loop_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=2)

	clip = Clip(source=os.path.join(clipPath,clipFilename))
	clip.gain = gain
	clip.rate = loopRate
	clip.loop = True
	clip.trigger()
	clip >> output

	yield duration

	output.close()


def clip_test():
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=2)

	clip = Clip(source=os.path.join(clipPath,clipFilename))
	clip.gain = gain
	clip >> output

	rate = 2.0
	numSteps = 10
	for ix in xrange(numSteps):
		clip.rate = rate
		duration = clip.duration()
		print "playing at rate %s for %s msec" % (rate,duration/zook.msec)
		clip.trigger()
		yield duration
		rate /= 2.0**(1.0/numSteps)

	for rate in [1.0,-1.0,2.0,-2.0,0.5,-0.5]:
		clip.rate = rate
		duration = clip.duration() * 1.10
		print "playing at rate %s for %s msec" % (rate,duration/zook.msec)
		clip.trigger()
		yield duration

	for ix in xrange(10):
		rate = (2*randint(0,1)-1) * (.8+.4*unit_random())
		clip.rate = rate
		print "playing at rate %s for %s msec" % (rate,250)
		clip.trigger()
		yield 250*zook.msec

	output.close()


if __name__ == "__main__": main()
