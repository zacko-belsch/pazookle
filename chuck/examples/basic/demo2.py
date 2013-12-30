#!/usr/bin/env python

# pazookle rewrite of the chuck example from
#	chuck.cs.princeton.edu/doc/examples/basic/demo2.ck

from pazookle.shred    import zook
from pazookle.ugen     import PassThru
from pazookle.generate import SinOsc
from pazookle.output   import WavOut


def main():
	zook.spork(demo2(True))
	zook.run()


def demo2(useLoop):
	output = WavOut(name="wave",filename="basic_demo2.ck.wav",channels=1)

	master = PassThru()                # global gain
	master.gain = 0.1
	master >> output

	if (useLoop):
		oscarray = [None] * 6          # connect
		for i in xrange(5):
			oscarray[i] = SinOsc(gain=1)
			oscarray[i] >> master
			oscarray[i].freq = 2**i * 110
			yield zook.sec

		for i in xrange(5):            # disconnect
			oscarray[i] // master
			yield zook.sec

	else:
		a = SinOsc(gain=1)             # connect
		a >> master
		a.freq = 110
		yield zook.sec

		b = SinOsc(gain=1)
		b >> master
		b.freq = 220
		yield zook.sec

		c = SinOsc(gain=1)
		c >> master
		c.freq = 440
		yield zook.sec

		d = SinOsc(gain=1)
		d >> master
		d.freq = 880
		yield zook.sec

		e = SinOsc(gain=1)
		e >> master
		e.freq = 1760
		yield zook.sec

		a // master                    # disconnect
		yield zook.sec

		b // master
		yield zook.sec

		c // master
		yield zook.sec

		d // master
		yield zook.sec

		e // master
		yield zook.sec

	output.close()


if __name__ == "__main__": main()
