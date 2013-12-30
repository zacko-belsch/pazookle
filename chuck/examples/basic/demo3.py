#!/usr/bin/env python

# pazookle rewrite of the chuck example from
#	chuck.cs.princeton.edu/doc/examples/basic/demo3.ck

from pazookle.shred    import zook
from pazookle.ugen     import PassThru
from pazookle.generate import SinOsc
from pazookle.output   import WavOut


def main():
	zook.spork(demo3())
	zook.run()


def demo3():
	output = WavOut(name="wave",filename="basic_demo3.ck.wav",channels=1)

	g = PassThru()                     # global gain
	g >> output
	g.gain = 0.5                       # set gain

	freq = 110.0
	x    = 6

	while (x > 0):                     # loop
		s = SinOsc(gain=1)             # connect to gain
		s >> g
		s.freq = freq                  # change frequency
		freq = freq * 2
		x -= 1                         # decrement x

		yield zook.sec                 # advance time by 1 second
		s // g                         # disconnect the sinosc

	output.close()

if __name__ == "__main__": main()
