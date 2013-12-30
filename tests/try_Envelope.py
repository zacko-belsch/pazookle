#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from random            import seed as random_seed,randint,uniform as urandom
from pazookle.shred    import zook,now,Shreduler
from pazookle.ugen     import UGen,PassThru
from pazookle.generate import SinOsc,SawOsc,TriOsc,SqrOsc
from pazookle.envelope import Envelope,ADSR
from pazookle.buffer   import Delay
from pazookle.output   import WavOut
from pazookle.midi     import build_scale,midi_to_freq
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --seed=<string>       random number generator seed
  --show:envelope       just show the envelope (no oscillator)
  <osc class>           one of SinOsc,SawOsc,TriOsc,SqrOsc
  --duty=<value>        set the oscillator's duty cycle
  --gain=<value>        set the gain
  ADSR                  use ADSR instead of AR envelope
  --attack=<msecs>      attack duration
  --decay=<msecs>       decay duration
  --sustain=<number>    sustain level
  --release=<msecs>     release duration
  --delays=<number>     number of reverb delay objects to use (default is none)
  --quarter=<seconds>   length of a quarter note
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global showEnvelope,oscType,duty,gain
	global envType,attack,decay,sustain,release
	global numDelays,quarterNote

	# parse the command line

	showEnvelope = False
	oscType      = SinOsc
	duty         = None
	gain         = 0.5
	envType      = Envelope
	attack       =  10 * zook.msec
	decay        = 150 * zook.msec
	sustain      = 0.2
	release      = 150 * zook.msec
	numDelays    = None
	quarterNote  = 0.3 * zook.sec
	duration     = 5.0
	debug        = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("--seed=")):
			random_seed(argVal)
		elif (arg == "--show:envelope"):
			showEnvelope = True
		elif (arg == "SinOsc"):
			oscType = SinOsc
		elif (arg == "SawOsc"):
			oscType = SawOsc
		elif (arg == "TriOsc"):
			oscType = TriOsc
		elif (arg == "SqrOsc"):
			oscType = SqrOsc
		elif (arg.startswith("--duty=")):
			duty = float_or_fraction(argVal)
		elif (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg == "ADSR"):
			envType = ADSR
		elif (arg.startswith("ADSR=")):
			envType = ADSR
			(attack,decay,sustain,release) = argVal.split(",")
			attack  = float_or_fraction(attack)  * zook.msec
			decay   = float_or_fraction(decay)   * zook.msec
			sustain = float_or_fraction(sustain)
			release = float_or_fraction(release) * zook.msec
		elif (arg.startswith("A=")) or (arg.startswith("--attack=")):
			attack = float_or_fraction(argVal) * zook.msec
		elif (arg.startswith("D=")) or (arg.startswith("--decay=")):
			decay = float_or_fraction(argVal) * zook.msec
		elif (arg.startswith("S=")) or (arg.startswith("--sustain=")):
			sustain = float_or_fraction(argVal)
		elif (arg.startswith("R=")) or (arg.startswith("--release=")):
			release = float_or_fraction(argVal) * zook.msec
		elif (arg.startswith("N=")) or (arg.startswith("--delays=")):
			numDelays = int(argVal)
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

	zook.spork(envelope_test(duration*zook.sec))
	zook.run()


def envelope_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=1)

	# set up scale

	Eb = 51                    # (51 is the midi note number for E-flat)
	minNote = 1
	maxNote = 29
	scale = build_scale("ionian",Eb,(minNote,maxNote))

	# set up chain

	if (showEnvelope): voice = None
	else:              voice = oscType(gain=gain)
	if (duty != None): voice.duty = duty
	if (envType == Envelope): envy = Envelope(ar=(attack,release))
	else:                     envy = ADSR(adsr=(attack,decay,sustain,release))
	master = PassThru()

	if (showEnvelope): envy >> master
	else:              voice >> envy >> master

	if (numDelays == None) or (numDelays <= 0):
		master >> output
	else:
		reverb = [None] * numDelays
		for ix in xrange(numDelays):
			reverb[ix] = Delay((60+20*ix)*zook.msec)
			master >> reverb[ix] >> reverb[ix] >> output
			reverb[ix].gain = 0.6

	# play random notes

	startTime = now()
	while (now() < startTime + duration):
		noteStart = now()

		degree = randint(minNote,maxNote)
		note   = scale[degree]
		freq   = midi_to_freq(note)
		if ("notes" in debug):
			print >>stderr, "%s\t%s\t%s" % (degree,note,freq)

		if (voice == None):
			envy.key_on(0.7)
		else:
			voice.freq = freq
			envy.key_on(urandom(0.5,1.0))
		yield ("absolute", noteStart + (quarterNote*0.9) - release)
		envy.key_off()
		yield ("absolute", noteStart + quarterNote)

	output.close()


if __name__ == "__main__": main()
