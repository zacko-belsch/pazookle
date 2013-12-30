#!/usr/bin/env python

import os.path
programName = os.path.splitext(os.path.basename(__file__))[0]

from sys               import argv,stdin,stderr,exit
from random            import seed as random_seed,randint,uniform as urandom
from pazookle.shred    import zook,now,Shreduler
from pazookle.ugen     import UGen,UGraph,PassThru
from pazookle.generate import SinOsc,SawOsc,TriOsc,SqrOsc
from pazookle.envelope import ADSR
from pazookle.buffer   import Delay
from pazookle.output   import WavOut
from pazookle.midi     import build_scale,midi_to_freq
from pazookle.parse    import float_or_fraction


def usage(s=None):
	message = """
usage: %s [options]
  --seed=<string>       random number generator seed
  <osc class>           one of SinOsc,SawOsc,TriOsc,SqrOsc
  --gain=<value>        set the gain
  --reverbgain=<value>  set gain for reverbs
  --echos=<times>       time in msec for each reverb (comma-separated list)
  --quarter=<seconds>   length of a quarter note
  --duration=<seconds>  length of the test""" \
  % programName

	if (s == None): exit (message)
	else:           exit ("%s\n%s" % (s,message))


def main():
	global debug
	global oscType,gain,reverbGain,echos,quarterNote

	# parse the command line

	oscType     = SinOsc
	gain        = 0.5
	reverbGain  = 0.6
	echos       = [60*zook.msec,80*zook.msec,100*zook.msec]
	quarterNote = 0.3 * zook.sec
	duration    = 3.0
	debug       = []

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
		elif (arg.startswith("RG=")) or (arg.startswith("--reverbgain=")):
			gain = float_or_fraction(argVal)
		elif (arg.startswith("E=")) or (arg.startswith("--echos=")):
			echos = [float_or_fraction(d)*zook.msec for d in argVal.split(",")]
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

	zook.spork(inlet_test(duration*zook.sec))
	zook.run()


def inlet_test(duration):
	filename = programName + ".wav"
	print >>stderr, "writing audio output to %s" % filename
	output = WavOut(filename=filename,channels=1)

	# set up scale

	Eb = 51                    # (51 is the midi note number for E-flat)
	minNote = 1
	maxNote = 29
	scale = build_scale("ionian",Eb,(minNote,maxNote))

	# set up chain

	attack  =  10*zook.msec
	decay   = 150*zook.msec
	sustain = 0.2
	release = 150*zook.msec

	voice  = oscType(gain=gain)
	envy   = ADSR(adsr=(attack,decay,sustain,release))
	reverb = SimpleReverb(gain=reverbGain,delayTime=echos)

	voice >> envy >> reverb >> output

	# play random notes

	startTime = now()
	while (now() < startTime + duration):
		noteStart = now()
		voice.freq = midi_to_freq(scale[randint(minNote,maxNote)])
		envy.key_on(urandom(0.5,1.0))
		yield ("absolute", noteStart + (quarterNote*0.9) - release)
		envy.key_off()
		yield ("absolute", noteStart + quarterNote)

	output.close()


class SimpleReverb(UGraph):
	"""Example of a graph with an inlet and outlets."""

	def __init__(self,name=None,channels=1,gain=None,delayTime=None):
		super(SimpleReverb,self).__init__(name=name)

		if (gain == None): gain = 0.6

		if (delayTime == None) or (delayTime == []):
			delayTime = [60*zook.msec]
		elif (type(delayTime) not in [list,tuple]):
			delayTime = [delayTime]

		self.inlet = collector = PassThru()
		self.outlet = [collector]
		for time in delayTime:
			reverb = Delay(time)
			reverb.gain = gain
			collector >> reverb >> reverb
			self.outlet += [reverb]


if __name__ == "__main__": main()

