#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from random            import seed as random_seed,uniform as urandom
from pazookle.shred    import zook,now,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import SinOsc,TriOsc
from pazookle.envelope import ADSR
from pazookle.buffer   import Echo
from pazookle.output   import WavOut
from pazookle.midi     import midi_to_freq
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --seed=<string>       random number generator seed
  --gain=<value>        set the gain
  --mix=<value>         set the wet/dry mix (0 means no echo, 1 means all echo)
  --channels=<1|2>      number of output channels
  --quarter=<seconds>   length of a quarter note
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global gain,delay,numChannels,mix,quarterNote

	# parse the command line
	# try M=5/7 G=3

	gain        = 0.7
	delay       = 100 * zook.msec
	numChannels = 1
	mix         = 0.5
	quarterNote = 0.3 * zook.sec
	duration    = 3.0
	debug       = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("--seed=")):
			random_seed(argVal)
		elif (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("D=")) or (arg.startswith("--delay=")):
			delay = float_or_fraction(argVal) * zook.msec
		elif (arg.startswith("--channels=")):
			numChannels = int(argVal)
		elif (arg.startswith("M=")) or (arg.startswith("--mix=")):
			mix = float_or_fraction(argVal)
		elif (arg.startswith("Q=")) or (arg.startswith("--quarter=")):
			quarterNote = float_or_fraction(argVal) * zook.sec
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

	zook.spork(echo_test(duration*zook.sec))
	zook.run()


def echo_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=numChannels)

	# create sound chain;  basically we'll have
	#   voice >> envy >> echo >> output
	# but voice may be two different ugens, fed into the envelope's left and
	# right channels

	voice = TriOsc(gain=gain)
	if (numChannels == 1): voice2 = None
	else:                  voice2 = SinOsc(gain=gain)

	attack  =  10*zook.msec
	decay   = 150*zook.msec
	sustain = 0.2
	release = 150*zook.msec

	envy  = ADSR(adsr=(attack,decay,sustain,release),channels=numChannels)
	echo  = Echo(delay=delay,channels=numChannels,mix=mix)

	if (voice2 != None):
		voice  >> envy["left"]
		voice2 >> envy["right"]
	else:
		voice >> envy

	envy >> echo >> output

	# play random notes

	startTime = now()
	while (now() < startTime + duration):
		noteStart = now()

		voice.freq = midi_to_freq(urandom(50,80))
		if (voice2 != None): voice2.freq = midi_to_freq(urandom(50,80))

		envy.key_on(urandom(0.5,1.0))
		yield ("absolute", noteStart + (quarterNote*0.9) - release)
		envy.key_off()
		yield ("absolute", noteStart + quarterNote)

	output.close()


if __name__ == "__main__": main()
