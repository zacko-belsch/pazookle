#!/usr/bin/env python
"""
bowed_string

Demonstrate a "violin" sound.  This follows example 6.5 from "Programming for
Musicians and Digital Artists" by Kapur, Cook, Salazar and Wang.
"""

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from random            import seed as random_seed,randint
from pazookle.shred    import zook,now,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import SinOsc,SawOsc
from pazookle.envelope import ADSR
from pazookle.output   import WavOut
from pazookle.midi     import build_scale,midi_to_freq
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --gain=<value>        set the gain
  --vibgain=<value>     set the vibrato gain
  --vibfreq=<value>     set the vibrato frequency
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global gain,vibratoGain,vibratoFreq

	# parse the command line

	gain        = .8
	vibratoGain = 2.0
	vibratoFreq = 5.0
	duration    = 10.0
	debug       = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("VG=")) or (arg.startswith("--vibgain=")):
			vibratoGain = float_or_fraction(argVal)
		elif (arg.startswith("VF=")) or (arg.startswith("--vibfreq=")):
			vibratoFreq = float_or_fraction(argVal)
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

	zook.spork(bowed_string(duration*zook.sec))
	zook.run()


def bowed_string(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=1)

	# create a scale, one octave of a C ionian

	C = 48                     # (48 is the midi note number for C)
	oneOctave = 7+1            # (one 7-note octave plus root on both ends)
	scale = build_scale("ionian",C,oneOctave)

	# create the sound chain;  this is a saw wave with frequency modulated by
	# a low frequency oscillator to create vibrato

	vibrato = SinOsc()
	violin  = SawOsc(gain=gain)
	envy    = ADSR(adsr=(500*zook.msec,100*zook.msec,.6,500*zook.msec))

	vibrato.gain = vibratoGain
	vibrato.freq = vibratoFreq

	vibrato >> violin["freq"] >> envy >> output

	# generate a series of notes, playing up the scale

	degree = 0

	startTime = now()
	while (now() < startTime + duration):
		note = scale[degree]
		freq = midi_to_freq(note)
		if ("notes" in debug):
			print >>stderr, "%s\t%s\t%s" % (degree,note,freq)
		degree = (degree + 1) % len(scale)

		vibrato.bias = freq - vibratoGain
		envy.key_on()
		yield 900*zook.msec
		envy.key_off()
		yield 200*zook.msec


if __name__ == "__main__": main()
