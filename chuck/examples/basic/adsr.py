#!/usr/bin/env python

# pazookle rewrite of the chuck example from
#	chuck.cs.princeton.edu/doc/examples/basic/adsr.ck
# "an ADSR envelope"

from random            import randint
from pazookle.shred    import zook,now
from pazookle.generate import SinOsc
from pazookle.envelope import ADSR
from pazookle.output   import WavOut
from pazookle.midi     import midi_to_freq

def main():
	zook.spork(adsr())
	zook.run()


def adsr():
	output = WavOut(name="wave",filename="basic_adsr.ck.wav",channels=1)

	s = SinOsc()
	e = ADSR()
	s >> e >> output

	e.set(10*zook.msec, 8*zook.msec, .5, 500*zook.msec) # set a, d, s, and r
	s.gain = .5                                         # set gain

	later = now() + 5*zook.sec
	while (now() < later):                              # finite loop
		s.freq = midi_to_freq(randint(20,120))          # choose freq
		e.keyOn()                                       # key on - start attack
		yield 500*zook.msec                             # advance time by 500 ms
		e.keyOff()                                      # key off - start release
		yield 800*zook.msec                             # advance time by 800 ms

	output.close()

if __name__ == "__main__": main()
