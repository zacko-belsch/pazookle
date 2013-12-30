#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from pazookle.shred    import zook,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import SinOsc,TriOsc,SqrOsc
from pazookle.output   import WavOut
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  <class>              TriOsc or SqrOsc
  --duty=<value>       set the triangle wave duty
  --duty=LFO           set the triangle wave duty to an LFO
  --gain=<value>       set the gain
  --freq=<value>       set the frequency
  --phase=<value>      set the phase
  --lfofreq=<value>    set the frequency of the lfo
  --duration=<seconds> length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global oscType,duty,gain,freq,phase,lfoFreq

	# parse the command line

	oscType  = TriOsc
	duty     = 0.5
	gain     = 0.5
	freq     = 440.0
	phase    = 0.0
	lfoFreq  = None
	duration = 1.0
	debug    = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg == "TriOsc"):
			oscType = TriOsc
		elif (arg == "SqrOsc"):
			oscType = SqrOsc
		elif (arg.startswith("D=")) or (arg.startswith("--duty=")):
			if (argVal == "LFO"): duty = "LFO"
			else:                 duty = float_or_fraction(argVal)
		elif (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("F=")) or (arg.startswith("--freq=")) or (arg.startswith("--frequency=")):
			freq = float_or_fraction(argVal)
		elif (arg.startswith("LF=")) or (arg.startswith("--lfofreq=")):
			lfoFreq = float_or_fraction(argVal)
		elif (arg.startswith("P=")) or (arg.startswith("--phase=")):
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

	if (lfoFreq != None): duty = "LFO"
	if (duty == "LFO") and (lfoFreq == None): lfoFreq = 0.5

	# run the test

	UGen.set_debug(debug)
	Shreduler.set_debug(debug)

	zook.spork(duty_test(duration*zook.sec))
	zook.run()


def duty_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=1)

	dutyContol = None
	if (duty == "LFO"):
		dutyContol = SinOsc()
		dutyContol.bias = 0.5
		dutyContol.gain = 0.45
		dutyContol.freq = lfoFreq

	a = oscType(gain=gain,freq=freq,phase=phase)
	if (dutyContol != None): a.duty = dutyContol
	else:                    a.duty = duty

	a >> output
	yield duration
	output.close()


if __name__ == "__main__": main()
