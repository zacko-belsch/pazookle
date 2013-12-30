#!/usr/bin/env python

# pazookle rewrite of the chuck example from
#	chuck.cs.princeton.edu/doc/examples/basic/envelope.ck
# "run white noise through envelope"

from random            import uniform as urandom
from pazookle.shred    import zook
from pazookle.generate import Noise
from pazookle.envelope import Envelope
from pazookle.output   import WavOut

def main():
	zook.spork(envelope())
	zook.run()


def envelope():
	output = WavOut(name="wave",filename="basic_envelope.ck.wav",channels=1)

	n = Noise(gain=1)                        # run white noise through envelope
	e = Envelope()
	n >> e >> output

	later = zook.now() + 5*zook.sec
	while (zook.now() < later):              # finite loop
		t = urandom(10,500) * zook.msec      # random choose rise/fall time
		#e.set(t,t)
		e.attack  = t
		e.release = t
		print "rise/fall: %s msec" % (t/zook.msec)

		e.keyOn()                            # key on - start attack
		yield 800*zook.msec                  # advance time by 800 ms
		e.keyOff()                           # key off - start release
		yield 800*zook.msec                  # advance time by 800 ms

	output.close()

if __name__ == "__main__": main()
