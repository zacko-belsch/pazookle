#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys             import argv,stdin,stderr,exit
from pazookle.shred  import zook,Shreduler
from pazookle.ugen   import UGen
from pazookle.ugen   import PassThru
from pazookle.buffer import Delay
from pazookle.output import WavOut
from kiss_noise      import KissNoise


def main():
	global debug

	debug = []

	# run the test

	UGen.set_debug(debug)
	Shreduler.set_debug(debug)

	zook.spork(filter_test(3*zook.sec))
	zook.run()


def filter_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=1)

	radius   = .99999
	delayLen = 500

	nosey  = KissNoise(seed=13013,gain=1)
	delay  = Delay(delay=delayLen,gain=radius**delayLen)
	master = PassThru()

	nosey >> master >> output
	master >> delay >> master

	yield duration
	output.close()


if __name__ == "__main__": main()
