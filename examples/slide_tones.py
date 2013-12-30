#!/usr/bin/env python
"""
slide_tones

Choose random quarter notes from a scale, and "slide" the frequency from one to
the next using a smooth cubic ramp.
"""

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from random            import seed as random_seed,randint,choice as random_choice
from pazookle.shred    import zook,now,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import SinOsc,SawOsc,TriOsc,SqrOsc
from pazookle.envelope import CubicRamp
from pazookle.output   import WavOut
from pazookle.midi     import build_pentatonic_scale,midi_to_freq
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --seed=<string>       random number generator seed
  <osc class>           one of SinOsc,SawOsc,TriOsc,SqrOsc
  --gain=<value>        set the gain
  --beat=<value>        set the tempo/beat (beats per minute)
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global oscType,gain,tempo

	# parse the command line

	oscType  = TriOsc
	gain     = 0.2
	tempo    = 400
	duration = 10.0
	debug    = []

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
		elif (arg.startswith("B=")) or (arg.startswith("--beat=")):
			tempo = float_or_fraction(argVal)
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

	zook.spork(slide_tones(duration*zook.sec))
	zook.run()


def slide_tones(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=1)

	# define timing

	quarterNote = 60*zook.sec / float(tempo)
	slideDur    = quarterNote / 4.5

	# create a scale, two octaves of an Eb pentatonic

	Eb = 51                    # (51 is the midi note number for E-flat)
	twoOctaves = 2*5+1         # (two 5-note octaves plus root on both ends)
	scale = build_pentatonic_scale("IV",Eb,twoOctaves)
	print "scale=[%s]" % ",".join([str(note) for note in scale])

	# create the sound chain;  this is a simple oscillator but with the
	# frequency controlled by a ramp object;  the ramp parameters will be
	# set inside the loop

	slide = CubicRamp()
	oscar = oscType(gain=gain)
	oscar.freq = slide
	oscar >> output

	# generate a series of random notes;  for each note we choose a random
	# frequency and use the ramp object to "slide" the oscillator from the old
	# frequency to the new

	prevFreq = 0.0
	startTime = now()
	while (now() < startTime + duration):
		noteStart = now()
		endOfNote = noteStart + quarterNote

		freq = midi_to_freq(random_choice(scale))
		if (freq < prevFreq):
			# slide down to the new frequency in one application of the ramp
			print "sliding from %.1f to %.1f" % (prevFreq,freq)
			slide.trigger(freq,slideDur)
			yield slideDur
		else:
			# slide up past, then down to, the new frequency in two
			# applications of the ramp
			overshootRatio = randint(3,7)
			overshootFreq = freq * overshootRatio
			print "sliding from %.1f thru %.1f to %.1f" % (prevFreq,overshootFreq,freq)

			slide.trigger(overshootFreq,slideDur/2)
			yield slideDur/2
			slide.trigger(freq,slideDur/2)
			yield slideDur/2

		# hold the note frequency steady for the remainger of the quarter note
		yield ("absolute",endOfNote)
		prevFreq = freq;

	output.close()


if __name__ == "__main__": main()
