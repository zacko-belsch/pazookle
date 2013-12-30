#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import Noise
from pazookle.filter   import LowPass
from pazookle.output   import WavOut
from kiss_noise        import KissNoise


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

	nosey = KissNoise(seed=13013,gain=1)
	phil  = LowPass(freq=400,Q=7,gain=1)

	nosey >> phil >> output

	yield duration
	output.close()


if __name__ == "__main__": main()
