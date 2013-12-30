#!/usr/bin/env python

# pazookle rewrite of the chuck example from
#	chuck.cs.princeton.edu/doc/examples/basic/comb.ck
# "a simple comb filter"

from math              import log
from pazookle.shred    import zook
from pazookle.ugen     import PassThru
from pazookle.buffer   import Delay
from pazookle.envelope import Impulse
from pazookle.output   import WavOut

def main():
	zook.spork(comb())
	zook.run()


def comb():
	output = WavOut(name="wave",filename="basic_comb.ck.wav",channels=1)

	imp    = Impulse()
	delay  = Delay()
	master = PassThru()

	imp >> master >> output                       # feedforward
	master >> delay >> master                     # feedback

	R = .99999                                    # our radius
	L = 500                                       # our delay order
	delay.delay = L                               # set delay
	delay.gain  = R**L                            # set dissipation factor
	imp.trigger(1)                                # fire impulse

	duration = log(.0001) / log(R)
	print "delay.gain = %s"      % delay.gain
	print "duration   = %s secs" % (duration / zook.sec)
	yield duration                                # advance time

	output.close()

if __name__ == "__main__": main()
