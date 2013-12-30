#!/usr/bin/env python
"""
triangle_wave_tooter

Demonstrate an "instrument" comprised of a triangle wave with varing duty
cycle.  For a square wave, varying the duty cycle makes it equivalent to a
pulse wave.  For a triangle wave, varying the duty cycle controls where the
peak occurs within each cycle.
"""

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from random            import seed as random_seed,uniform as urandom, \
                              choice as random_choice
from pazookle.shred    import zook,now,Shreduler
from pazookle.ugen     import UGen
from pazookle.generate import SinOsc,TriOsc,SqrOsc
from pazookle.envelope import ADSR
from pazookle.output   import WavOut
from pazookle.midi     import build_scale,midi_to_freq
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --seed=<string>       random number generator seed
  <osc class>           one of TriOsc,SqrOsc
  --lfofreq=<value>     set the frequency of the cuty-cycle control LFO
  --gain=<value>        set the gain
  ADSR                  use ADSR instead of AR envelope
  --attack=<msecs>      attack duration
  --decay=<msecs>       decay duration
  --sustain=<number>    sustain level
  --release=<msecs>     release duration
  --toot=<msec>         set the time from one toot to the next
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global oscType,lfoFreq,gain,attack,decay,sustain,release,tootTime

	# parse the command line

	oscType  = TriOsc
	lfoFreq  = 3.0
	gain     = .8
	attack   =  50 * zook.msec
	decay    = 150 * zook.msec
	sustain  = 0.6
	release  = 150 * zook.msec
	tootTime = 500 * zook.msec
	duration = 5.0
	debug    = []

	for arg in argv[1:]:
		if ("=" in arg):
			argVal = arg.split("=",1)[1]

		if (arg.startswith("--seed=")):
			random_seed(argVal)
		elif (arg == "TriOsc"):
			oscType = TriOsc
		elif (arg == "SqrOsc"):
			oscType = SqrOsc
		elif (arg.startswith("LF=")) or (arg.startswith("--lfofreq=")):
			lfoFreq = float_or_fraction(argVal)
		elif (arg.startswith("G=")) or (arg.startswith("--gain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("ADSR=")):
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
		elif (arg.startswith("Q=")) or (arg.startswith("--toot=")):
			tootTime = float_or_fraction(argVal) * zook.msec
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

	zook.spork(triangle_wave_tooter(duration*zook.sec))
	zook.run()


def triangle_wave_tooter(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=1)

	# create a scale, three octaves of a C ionian

	C = 48                     # (48 is the midi note number for C)
	threeOctaves = 3*7+1       # (three 7-note octaves plus root on both ends)
	scale = build_scale("ionian",C,threeOctaves)

	# create the sound chain;  this consists of an LFO to create a duty-cycle
	# that varies from .05 to .95, and a triangle wave (or a pulse wave) fed
	# through a standard ADSR envelope

	(dutyLow,dutyHigh) = (0.05,0.95)
	dutyContol = SinOsc(bias=(dutyHigh+dutyLow)/2.0,gain=(dutyHigh-dutyLow)/2.0)
	dutyContol.freq = lfoFreq

	tooter = oscType(gain=gain)
	envy   = ADSR(adsr=(attack,decay,sustain,release))

	dutyContol >> tooter["duty"] >> envy >> output

	# generate a series of random notes

	startTime = now()
	while (now() < startTime + duration):
		noteStart = now()

		tooter.freq = midi_to_freq(random_choice(scale))
		envy.key_on(urandom(0.5,1.0))
		envy.key_on()
		yield ("absolute", noteStart + (tootTime*0.9) - release)
		envy.key_off()
		yield ("absolute", noteStart + tootTime)


if __name__ == "__main__": main()
