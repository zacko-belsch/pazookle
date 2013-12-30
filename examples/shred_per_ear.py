#!/usr/bin/env python
"""
shred_per_ear

Send random quarter notes to each ear, controlled by two shreds.  Each shred
has it's own tempo.
"""

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from random            import seed as random_seed,choice as random_choice, \
                              uniform as urandom
from pazookle.shred    import zook,now,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import SinOsc,SawOsc,TriOsc,SqrOsc
from pazookle.envelope import ADSR
from pazookle.output   import WavOut
from pazookle.midi     import build_pentatonic_scale,midi_to_freq
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --seed=<string>        random number generator seed
  <class>                one of SinOsc,SawOsc,TriOsc,SqrOsc
  --gain=<value>         set the gain
  --leftbeat=<value>     set the tempo/beat for the left ear (beats per minute)
  --rightbeat=<value>    set the tempo/beat for the right ear
  --single=<left|right>  run the test on a single ear
  --duration=<seconds>   length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global oscType,gain,leftTempo,rightTempo,singleEar

	# parse the command line

	oscType    = TriOsc
	gain       = 0.5
	leftTempo  = 100
	rightTempo = 150
	duration   = 10.0
	singleEar  = None
	debug      = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("--seed=")):
			random_seed(argVal)
		elif (arg == "SinOsc"):
			oscType = SinOsc
		elif (arg == "SawOsc"):
			oscType = SawOsc
		elif (arg == "TriOsc"):
			oscType = TriOsc
		elif (arg == "SqrOsc"):
			oscType = SqrOsc
		elif (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("LB=")) or (arg.startswith("--leftbeat=")):
			leftTempo = float_or_fraction(argVal)
		elif (arg.startswith("RB=")) or (arg.startswith("--rightbeat=")):
			rightTempo = float_or_fraction(argVal)
		elif (arg.startswith("T=")) or (arg.startswith("--dur=")) or (arg.startswith("--duration=")):
			duration = float_or_fraction(argVal)
		elif (arg == "--single=left"):
			singleEar = "left"
		elif (arg == "--single=right"):
			singleEar = "right"
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

	zook.spork(shred_per_ear(duration*zook.sec))
	zook.run()


def shred_per_ear(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=2)

	# create a scale, two octaves of an Eb pentatonic

	Eb = 51                    # (51 is the midi note number for E-flat)
	twoOctaves = 2*5+1         # (two 5-note octaves plus root on both ends)
	leftScale  = build_pentatonic_scale("IV",Eb,twoOctaves)
	rightScale = [note+7 for note in leftScale]
	print "left  scale=[%s]" % ",".join([str(note) for note in leftScale])
	print "right scale=[%s]" % ",".join([str(note) for note in rightScale])

	# spork one shred for each ear

	if (singleEar != "right"):
		zook.spork(one_ear("left", leftScale, leftTempo, output,duration))
	if (singleEar != "left"):
		zook.spork(one_ear("right",rightScale,rightTempo,output,duration))

	# all shreds must have at least one yield;  that's what makes them
	# python generators, and all shreds are generators
	yield 0

	# wait 'til the child shreds are done then close the file
	# $$$ this is problematic, we need some means for this shred to wait for
	#     .. other shreds to finish
	#
	# yield duration
	# output.close()


def one_ear(whichEar,scale,tempo,output,duration):
	# define timing

	quarterNote = 60*zook.sec / float(tempo)

	# create the sound chain;  note that output["left"] and output["right"]
	# are connection syntax to isolate a single channel

	attack  =  10*zook.msec
	decay   = 150*zook.msec
	sustain = 0.2
	release = 150*zook.msec

	oscar = oscType(gain=gain)
	envy  = ADSR(adsr=(attack,decay,sustain,release))

	oscar >> envy >> output[whichEar]

	# generate a series of random notes

	prevFreq = 0.0
	startTime = now()
	while (now() < startTime + duration):
		noteStart = now()

		oscar.freq = freq = midi_to_freq(random_choice(scale))
		print "T=%.3f %-5s freq=%.1f" % (now()/zook.sec,whichEar,freq)

		envy.key_on(urandom(0.7,1.0))
		yield ("absolute", noteStart + (quarterNote*0.9) - envy._release)
		envy.key_off()
		yield ("absolute", noteStart + quarterNote)


if __name__ == "__main__": main()
